"""
这部分代码将被添加到 routes_new.py
包含工单系统路由和统一用户管理路由
"""

    # ==================== 工单系统路由 ====================

    @app.route('/case/')
    def case_index():
        """首页"""
        frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'case')
        return send_from_directory(frontend_dir, 'login.html')

    @app.route('/case/<path:filename>')
    def case_serve_frontend(filename):
        """提供前端静态文件"""
        try:
            frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'case')
            return send_from_directory(frontend_dir, filename)
        except:
            return "404 - 文件未找到", 404

    @app.route('/case/api/login', methods=['POST'])
    def case_login():
        """登录"""
        try:
            data = request.get_json()
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()

            if not username or not password:
                return error_response('用户名和密码不能为空', 400)

            # 使用统一认证
            success, result = authenticate_user(username, password)

            if not success:
                logger.warning(f"工单系统登录失败: {username}")
                return error_response(result, 401)

            user_info = result

            session['user_id'] = user_info['id']
            session['username'] = user_info['username']
            session['real_name'] = user_info.get('real_name') or user_info.get('display_name', '')
            session['role'] = user_info['role']
            session['display_name'] = user_info.get('display_name', '')

            logger.info(f"工单系统用户 {username} 登录成功")
            return success_response(
                data={
                    'user_id': user_info['id'],
                    'username': user_info['username'],
                    'real_name': user_info.get('real_name') or user_info.get('display_name', ''),
                    'role': user_info['role']
                },
                message='登录成功'
            )
        except Exception as e:
            log_exception(logger, "工单系统登录失败")
            return server_error_response(f'登录失败：{str(e)}')

    @app.route('/case/api/logout', methods=['POST'])
    def case_logout():
        """登出"""
        username = session.get('username', 'unknown')
        session.clear()
        logger.info(f"工单系统用户 {username} 登出")
        return success_response(message='登出成功')

    @app.route('/case/api/user/info', methods=['GET'])
    def case_get_user_info():
        """获取用户信息"""
        user_id = session.get('user_id')
        if not user_id:
            return unauthorized_response(message='未登录')

        return success_response(
            data={
                'user_id': session.get('user_id'),
                'username': session.get('username'),
                'real_name': session.get('real_name'),
                'role': session.get('role'),
                'email': session.get('email')
            },
            message='获取成功'
        )

    @app.route('/case/api/ticket', methods=['POST'])
    def case_create_ticket():
        """创建工单"""
        try:
            data = request.get_json()
            required_fields = [
                'customer_name', 'customer_contact', 'customer_email',
                'product', 'issue_type', 'priority', 'title', 'content'
            ]

            # 验证必填字段
            is_valid, errors = validate_required(data, required_fields)
            if not is_valid:
                return validation_error_response(errors)

            # 验证邮箱
            customer_email = data['customer_email'].strip()
            is_valid, msg = validate_email(customer_email)
            if not is_valid:
                return error_response('客户邮箱格式不合法', 400)

            # 验证枚举值
            valid_issue_types = ['technical', 'service', 'complaint', 'other']
            valid_priorities = ['low', 'medium', 'high', 'urgent']
            if data['issue_type'].strip() not in valid_issue_types:
                return error_response('问题类型值不合法', 400)
            if data['priority'].strip() not in valid_priorities:
                return error_response('优先级值不合法', 400)

            ticket_id = generate_ticket_id()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            conn = get_case_db_connection()
            if not conn:
                return server_error_response('数据库连接失败')
            cursor = conn.cursor()
            insert_sql = """
                INSERT INTO tickets (ticket_id, customer_name, customer_contact, customer_email,
                                    product, issue_type, priority, title, content,
                                    status, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (
                ticket_id, data['customer_name'].strip(), data['customer_contact'].strip(),
                customer_email, data['product'].strip(), data['issue_type'].strip(),
                data['priority'].strip(), data['title'].strip(), data['content'].strip(),
                'pending', now, now
            ))
            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"创建工单 {ticket_id} 成功")
            return success_response(message='工单创建成功', data={'ticket_id': ticket_id})
        except Exception as e:
            log_exception(logger, "创建工单失败")
            return server_error_response(f'工单创建失败：{str(e)}')

    @app.route('/case/api/tickets', methods=['GET'])
    def case_get_tickets():
        """获取工单列表"""
        try:
            user_role = session.get('role')
            user_username = session.get('username')

            if not user_role:
                return unauthorized_response(message='未登录')

            status = request.args.get('status', '').strip()
            conn = get_case_db_connection()
            if not conn:
                return server_error_response('数据库连接失败')
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            if user_role == 'customer' and user_username:
                if status:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE customer_name = %s AND status = %s ORDER BY create_time DESC
                    """
                    cursor.execute(select_sql, (user_username, status))
                else:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE customer_name = %s ORDER BY create_time DESC
                    """
                    cursor.execute(select_sql, (user_username,))
            elif user_role == 'admin':
                if status:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE status = %s ORDER BY create_time DESC
                    """
                    cursor.execute(select_sql, (status,))
                else:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets ORDER BY create_time DESC
                    """
                    cursor.execute(select_sql)
            else:
                tickets = []
                cursor.close()
                conn.close()
                return success_response(data=tickets, message='查询成功')

            tickets = cursor.fetchall()
            cursor.close()
            conn.close()

            for ticket in tickets:
                ticket['create_time'] = ticket['create_time'].strftime('%Y-%m-%d %H:%M:%S')

            return success_response(data=tickets, message='查询成功')
        except Exception as e:
            log_exception(logger, "获取工单列表失败")
            return server_error_response(f'查询失败：{str(e)}')

    @app.route('/case/api/ticket/<ticket_id>', methods=['GET'])
    def case_get_ticket_detail(ticket_id):
        """获取工单详情"""
        try:
            user_role = session.get('role')
            user_username = session.get('username')

            if not user_role:
                return unauthorized_response(message='未登录')

            conn = get_case_db_connection()
            if not conn:
                return server_error_response('数据库连接失败')
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            select_sql = "SELECT * FROM tickets WHERE ticket_id = %s"
            cursor.execute(select_sql, (ticket_id,))
            ticket = cursor.fetchone()
            cursor.close()
            conn.close()

            if not ticket:
                return not_found_response(message='工单不存在')

            if user_role == 'customer' and ticket['customer_name'] != user_username:
                return forbidden_response(message='无权访问此工单')

            ticket['create_time'] = ticket['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            ticket['update_time'] = ticket['update_time'].strftime('%Y-%m-%d %H:%M:%S')
            ticket['current_user_role'] = user_role

            return success_response(data=ticket, message='查询成功')
        except Exception as e:
            log_exception(logger, "获取工单详情失败")
            return server_error_response(f'查询失败：{str(e)}')

    @app.route('/case/api/ticket/<ticket_id>/status', methods=['PUT'])
    def case_update_ticket_status(ticket_id):
        """更新工单状态"""
        try:
            user_role = session.get('role')
            if not user_role or user_role != 'admin':
                return forbidden_response(message='无权执行此操作')

            data = request.get_json()
            new_status = data.get('status', '').strip()

            valid_statuses = ['pending', 'processing', 'completed', 'closed']
            if new_status not in valid_statuses:
                return error_response('工单状态值不合法', 400)

            conn = get_case_db_connection()
            if not conn:
                return server_error_response('数据库连接失败')
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM tickets WHERE ticket_id = %s", (ticket_id,))
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return not_found_response(message='工单不存在')

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_sql = "UPDATE tickets SET status = %s, update_time = %s WHERE ticket_id = %s"
            cursor.execute(update_sql, (new_status, now, ticket_id))
            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"更新工单 {ticket_id} 状态为 {new_status}")
            return success_response(message='工单状态更新成功')
        except Exception as e:
            log_exception(logger, "更新工单状态失败")
            return server_error_response(f'更新失败：{str(e)}')

    @app.route('/case/api/ticket/<ticket_id>/messages', methods=['GET'])
    def case_get_messages(ticket_id):
        """获取工单消息"""
        try:
            conn = get_case_db_connection()
            if not conn:
                return server_error_response('数据库连接失败')
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            select_sql = """
                SELECT id, ticket_id, sender, sender_name, content, send_time
                FROM messages WHERE ticket_id = %s ORDER BY send_time ASC
            """
            cursor.execute(select_sql, (ticket_id,))
            messages = cursor.fetchall()
            cursor.close()
            conn.close()

            for msg in messages:
                msg['send_time'] = msg['send_time'].strftime('%Y-%m-%d %H:%M:%S')

            return success_response(data=messages, message='查询成功')
        except Exception as e:
            log_exception(logger, "获取工单消息失败")
            return server_error_response(f'查询失败：{str(e)}')

    # ==================== 统一用户管理路由 ====================

    @app.route('/unified/users')
    @login_required(roles=['admin'])
    def unified_users():
        """统一用户管理页面"""
        return render_template('unified_user_management.html',
                             users=[],
                             error=None,
                             current_user=get_kb_current_user())

    # 统一用户管理API
    @app.route('/unified/api/users', methods=['GET'])
    @login_required(roles=['admin'])
    def unified_get_users():
        """获取统一用户列表"""
        try:
            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response('数据库连接失败')

            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM `users` ORDER BY created_at DESC")
            users = cursor.fetchall()
            cursor.close()
            conn.close()

            return success_response(data=users, message='查询成功')
        except Exception as e:
            log_exception(logger, "获取统一用户列表失败")
            return server_error_response(f'获取用户列表失败：{str(e)}')

    @app.route('/unified/api/users', methods=['POST'])
    @login_required(roles=['admin'])
    def unified_add_user():
        """添加统一用户"""
        try:
            data = request.get_json()

            # 验证输入
            is_valid, errors = validate_user_data(data)
            if not is_valid:
                return validation_error_response(errors)

            if not data.get('username') or not data.get('password'):
                return error_response('用户名和密码不能为空', 400)

            # 使用统一用户创建接口
            success, message = create_user(
                username=data['username'],
                password=data['password'],
                display_name=data.get('display_name'),
                real_name=data.get('real_name'),
                email=data.get('email', ''),
                role=data.get('role', 'user'),
                created_by=session.get('username', 'admin')
            )

            if success:
                logger.info(f"添加统一用户 {data['username']} 成功")
                return success_response(message=message)
            else:
                return error_response(message, 400)
        except Exception as e:
            log_exception(logger, "添加统一用户失败")
            return server_error_response(f'添加用户失败：{str(e)}')

    @app.route('/unified/api/users/<int:user_id>', methods=['PUT'])
    @login_required(roles=['admin'])
    def unified_update_user(user_id):
        """更新统一用户（使用新的UserService）"""
        try:
            data = request.get_json()
            if not data:
                return error_response('请求数据不能为空', 400)

            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response('数据库连接失败')

            # 输入验证
            is_valid, errors = validate_user_data(data)
            if not is_valid:
                conn.close()
                return validation_error_response(errors)

            # 调用服务层
            success, message = UserService.update_user(conn, user_id, data)
            conn.close()

            if success:
                logger.info(f"更新统一用户 {user_id} 成功")
                return success_response(message=message)
            else:
                return error_response(message, 400)

        except Exception as e:
            log_exception(logger, "更新统一用户失败")
            return server_error_response(f'更新用户失败：{str(e)}')

    @app.route('/unified/api/users/<int:user_id>', methods=['DELETE'])
    @login_required(roles=['admin'])
    def unified_delete_user(user_id):
        """删除统一用户（使用新的UserService）"""
        try:
            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response('数据库连接失败')

            # 检查是否是当前登录用户
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM `users` WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user and user[0] == session.get('username'):
                cursor.close()
                conn.close()
                return error_response('不能删除当前登录用户', 400)
            cursor.close()

            # 调用服务层
            success, message = UserService.delete_user(conn, user_id)
            conn.close()

            if success:
                logger.info(f"删除统一用户 {user_id} 成功")
                return success_response(message=message)
            else:
                return error_response(message, 400)

        except Exception as e:
            log_exception(logger, "删除统一用户失败")
            return server_error_response(f'删除用户失败：{str(e)}')

    # 兼容旧的 kb-users 路由（指向新的统一用户API）
    @app.route('/unified/api/kb-users', methods=['GET'])
    @login_required(roles=['admin'])
    def unified_get_kb_users():
        """获取知识库用户列表（兼容路由）"""
        return unified_get_users()

    @app.route('/unified/api/kb-users', methods=['POST'])
    @login_required(roles=['admin'])
    def unified_add_kb_user():
        """添加知识库用户（兼容路由）"""
        return unified_add_user()

    @app.route('/unified/api/kb-users/<int:user_id>', methods=['PUT'])
    @login_required(roles=['admin'])
    def unified_update_kb_user(user_id):
        """更新知识库用户（兼容路由）"""
        return unified_update_user(user_id)

    @app.route('/unified/api/kb-users/<int:user_id>', methods=['DELETE'])
    @login_required(roles=['admin'])
    def unified_delete_kb_user(user_id):
        """删除知识库用户（兼容路由）"""
        return unified_delete_user(user_id)

    # 工单系统用户管理API（现在使用统一用户表）
    @app.route('/unified/api/case-users', methods=['GET'])
    @login_required(roles=['admin'])
    def unified_get_case_users():
        """获取工单系统用户列表"""
        try:
            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response('数据库连接失败')

            cursor = conn.cursor(pymysql.cursors.DictCursor)
            # 只返回工单系统相关的角色
            cursor.execute("""
                SELECT id, username, display_name, real_name, role, email, created_at as create_time
                FROM `users`
                WHERE role IN ('admin', 'customer')
                ORDER BY created_at DESC
            """)
            users = cursor.fetchall()
            cursor.close()
            conn.close()

            return success_response(data=users, message='查询成功')
        except Exception as e:
            log_exception(logger, "获取工单系统用户列表失败")
            return server_error_response(f'获取用户列表失败：{str(e)}')

    @app.route('/unified/api/case-users', methods=['POST'])
    @login_required(roles=['admin'])
    def unified_add_case_user():
        """添加工单系统用户"""
        try:
            data = request.get_json()

            # 验证输入
            is_valid, errors = validate_user_data(data)
            if not is_valid:
                return validation_error_response(errors)

            if not data.get('username') or not data.get('password') or not data.get('email'):
                return error_response('用户名、密码和邮箱不能为空', 400)

            # 使用统一用户创建接口
            success, message = create_user(
                username=data['username'],
                password=data['password'],
                display_name=data.get('real_name', ''),
                real_name=data.get('real_name', ''),
                email=data['email'],
                role=data.get('role', 'customer'),
                created_by=session.get('username', 'admin')
            )

            if success:
                logger.info(f"添加工单系统用户 {data['username']} 成功")
                return success_response(message=message)
            else:
                return error_response(message, 400)
        except Exception as e:
            log_exception(logger, "添加工单系统用户失败")
            return server_error_response(f'添加用户失败：{str(e)}')

    @app.route('/unified/api/case-users/<int:user_id>', methods=['PUT'])
    @login_required(roles=['admin'])
    def unified_update_case_user(user_id):
        """更新工单系统用户（使用新的UserService）"""
        try:
            data = request.get_json()
            if not data:
                return error_response('请求数据不能为空', 400)

            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response('数据库连接失败')

            # 输入验证
            is_valid, errors = validate_user_data(data)
            if not is_valid:
                conn.close()
                return validation_error_response(errors)

            # 调用服务层
            success, message = UserService.update_user(conn, user_id, data)
            conn.close()

            if success:
                logger.info(f"更新工单系统用户 {user_id} 成功")
                return success_response(message=message)
            else:
                return error_response(message, 400)

        except Exception as e:
            log_exception(logger, "更新工单系统用户失败")
            return server_error_response(f'更新用户失败：{str(e)}')

    @app.route('/unified/api/case-users/<int:user_id>', methods=['DELETE'])
    @login_required(roles=['admin'])
    def unified_delete_case_user(user_id):
        """删除工单系统用户（使用新的UserService）"""
        try:
            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response('数据库连接失败')

            # 检查是否是当前登录用户
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM `users` WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user and user[0] == session.get('username'):
                cursor.close()
                conn.close()
                return error_response('不能删除当前登录用户', 400)
            cursor.close()

            # 调用服务层
            success, message = UserService.delete_user(conn, user_id)
            conn.close()

            if success:
                logger.info(f"删除工单系统用户 {user_id} 成功")
                return success_response(message=message)
            else:
                return error_response(message, 400)

        except Exception as e:
            log_exception(logger, "删除工单系统用户失败")
            return server_error_response(f'删除用户失败：{str(e)}')

    # 用户统计API
    @app.route('/unified/api/user-stats', methods=['GET'])
    @login_required(roles=['admin'])
    def unified_get_user_stats():
        """获取用户统计信息"""
        try:
            stats = {
                'users': {'total': 0, 'active': 0, 'admins': 0, 'customers': 0, 'kb_users': 0},
                'login_logs': {'total': 0, 'today': 0, 'success': 0, 'failed': 0}
            }

            # 统一用户表统计
            conn = get_unified_kb_conn()
            if conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)

                # 总用户数
                cursor.execute("SELECT COUNT(*) as total FROM `users`")
                stats['users']['total'] = cursor.fetchone()['total']

                # 活跃用户数
                cursor.execute("SELECT COUNT(*) as count FROM `users` WHERE status = 'active'")
                stats['users']['active'] = cursor.fetchone()['count']

                # 管理员数量
                cursor.execute("SELECT COUNT(*) as count FROM `users` WHERE role = 'admin'")
                stats['users']['admins'] = cursor.fetchone()['count']

                # 客户数量
                cursor.execute("SELECT COUNT(*) as count FROM `users` WHERE role = 'customer'")
                stats['users']['customers'] = cursor.fetchone()['count']

                # 知识库用户数
                cursor.execute("SELECT COUNT(*) as count FROM `users` WHERE role IN ('admin', 'user')")
                stats['users']['kb_users'] = cursor.fetchone()['count']

                # 登录日志统计
                cursor.execute("SELECT COUNT(*) as total FROM mgmt_login_logs")
                stats['login_logs']['total'] = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as count FROM mgmt_login_logs WHERE DATE(login_time) = CURDATE()")
                stats['login_logs']['today'] = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM mgmt_login_logs WHERE status = 'success'")
                stats['login_logs']['success'] = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM mgmt_login_logs WHERE status = 'failed'")
                stats['login_logs']['failed'] = cursor.fetchone()['count']

                cursor.close()
                conn.close()

            logger.info("获取用户统计信息成功")
            return success_response(data=stats, message='查询成功')
        except Exception as e:
            log_exception(logger, "获取用户统计信息失败")
            return server_error_response(f'获取统计信息失败：{str(e)}')

    # 管理员重置用户密码路由
    @app.route('/auth/api/reset-password/<int:user_id>', methods=['POST'])
    @login_required(roles=['admin'])
    def reset_user_password(user_id):
        """管理员重置指定用户的密码"""
        try:
            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response('数据库连接失败')

            cursor = conn.cursor()

            # 获取用户信息
            cursor.execute("SELECT username FROM `users` WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                cursor.close()
                conn.close()
                return not_found_response(message='用户不存在')

            username = user[0]

            # 检查是否是admin用户
            if username == 'admin':
                cursor.close()
                conn.close()
                return error_response('不能重置admin用户密码', 400)

            data = request.get_json()
            new_password = data.get('password', '').strip()

            if not new_password:
                return error_response('请输入新密码', 400)

            # 验证新密码
            is_valid, msg = validate_password(new_password)
            if not is_valid:
                return error_response(msg, 400)

            # 生成新的 werkzeug 密码哈希
            password_hash = generate_password_hash(new_password)

            update_sql = "UPDATE `users` SET password_hash = %s, password_type = %s, updated_at = NOW() WHERE id = %s"
            cursor.execute(update_sql, (password_hash, 'werkzeug', user_id))
            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"管理员重置用户 {username} 的密码成功")
            return success_response(message=f'用户 {username} 的密码已重置')
        except Exception as e:
            log_exception(logger, "重置用户密码失败")
            return server_error_response(f'重置密码失败：{str(e)}')
