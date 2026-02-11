"""
工单系统路由蓝图
"""
from flask import Blueprint, request, render_template, session, jsonify
from common.response import success_response, error_response, unauthorized_response, server_error_response
from common.unified_auth import get_current_user, authenticate_user
from common.validators import validate_email, validate_required, validate_phone
from common.logger import logger, log_request, log_exception
from common.database_context import db_connection
from datetime import datetime
import pymysql

case_bp = Blueprint('case', __name__, url_prefix='/case')


def generate_ticket_id():
    """生成唯一工单ID"""
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    import uuid
    random_str = str(uuid.uuid4())[:6].upper()
    return f"TK-{now}-{random_str}"


@case_bp.route('/')
def index():
    """首页"""
    return render_template('case/login.html')


@case_bp.route('/api/login', methods=['POST'])
def login():
    """工单系统登录
    
    用户登录工单系统
    ---
    tags:
      - 工单-认证
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: 用户名
            password:
              type: string
              description: 密码
    responses:
      200:
        description: 登录成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      401:
        description: 登录失败
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        log_request(logger, request)
        # 支持两种提交方式：JSON 和 表单
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # 简单验证用户名和密码
        if not username:
            return error_response(message='用户名不能为空')
        if not password:
            return error_response(message='密码不能为空')
        
        # 使用统一认证
        success, result = authenticate_user(username, password)
        
        if not success:
            return unauthorized_response(message=result)
        
        user_info = result
        
        session['user_id'] = user_info['id']
        session['username'] = user_info['username']
        session['real_name'] = user_info.get('real_name') or user_info.get('display_name', '')
        session['role'] = user_info['role']
        session['display_name'] = user_info.get('display_name', '')
        
        return success_response(data={
            'user_id': user_info['id'],
            'username': user_info['username'],
            'real_name': user_info.get('real_name') or user_info.get('display_name', ''),
            'role': user_info['role']
        }, message='登录成功')
    except Exception as e:
        log_exception(logger, "登录失败")
        return server_error_response(message=f'登录失败：{str(e)}')


@case_bp.route('/api/logout', methods=['POST'])
def logout():
    """登出"""
    session.clear()
    return success_response(message='登出成功')


@case_bp.route('/api/user/info', methods=['GET'])
def get_user_info():
    """获取用户信息"""
    user_id = session.get('user_id')
    if not user_id:
        return unauthorized_response(message='未登录')

    return success_response(data={
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'real_name': session.get('real_name'),
        'role': session.get('role'),
        'email': session.get('email')
    })


@case_bp.route('/api/admins', methods=['GET'])
def get_admins():
    """获取管理员和普通用户列表（用于工单分配）"""
    try:
        log_request(logger, request)

        # 检查权限，只有 admin 和 user 角色可以查看
        user_role = session.get('role')
        if user_role not in ['admin', 'user']:
            return unauthorized_response(message='权限不足')

        with db_connection('kb') as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # 查询 admin 和 user 角色的活跃用户
            select_sql = """
                SELECT id, username, real_name, display_name, role, email
                FROM `users`
                WHERE role IN ('admin', 'user') AND status = 'active'
                ORDER BY role, username
            """
            cursor.execute(select_sql)
            users = cursor.fetchall()

        # 格式化用户数据，优先使用 real_name
        formatted_users = []
        for user in users:
            name = user.get('real_name') or user.get('display_name') or user.get('username', '')
            formatted_users.append({
                'id': user['id'],
                'username': user['username'],
                'name': name,
                'role': user['role'],
                'email': user.get('email', '')
            })

        return success_response(data=formatted_users, message='查询成功')
    except Exception as e:
        log_exception(logger, "查询用户列表失败")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return server_error_response(message=f'查询失败：{str(e)}')


@case_bp.route('/api/ticket', methods=['POST'])
def create_ticket():
    """创建工单

    创建新的工单
    ---
    tags:
      - 工单-操作
    security:
      - CookieAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - customer_name
            - customer_contact_phone
            - customer_email
            - product
            - issue_type
            - priority
            - title
            - content
          properties:
            customer_name:
              type: string
              description: 客户名称（公司名）
            customer_contact_name:
              type: string
              description: 客户联系人姓名（当前登录用户）
            customer_contact_phone:
              type: string
              description: 联系电话
            customer_email:
              type: string
              format: email
              description: 联系邮箱
            product:
              type: string
              description: 涉及产品
            issue_type:
              type: string
              enum: [technical, service, complaint, other]
              description: 问题类型
            priority:
              type: string
              enum: [low, medium, high, urgent]
              description: 优先级
            title:
              type: string
              description: 工单标题
            content:
              type: string
              description: 工单详情
    responses:
      200:
        description: 创建成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: 参数错误
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        log_request(logger, request)
        # 支持两种提交方式：JSON 和 表单
        if request.is_json:
            data = request.get_json()
        else:
            # 获取表单数据
            data = request.form.to_dict()

        user_role = session.get('role')
        user_real_name = session.get('real_name', '')
        user_username = session.get('username', '')
        user_email = session.get('email', '')

        required_fields = [
            'customer_name', 'customer_contact_phone', 'customer_email',
            'product', 'issue_type', 'priority', 'title', 'content'
        ]

        # 验证必填字段
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return error_response(message=f'缺少必填字段：{field}或字段值为空')
        
        customer_email = data['customer_email'].strip()
        is_valid, error_msg = validate_email(customer_email)
        if not is_valid:
            return error_response(message=error_msg)
        
        valid_issue_types = ['technical', 'service', 'complaint', 'other']
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if data['issue_type'].strip() not in valid_issue_types:
            return error_response(message='问题类型值不合法')
        if data['priority'].strip() not in valid_priorities:
            return error_response(message='优先级值不合法')
        
        ticket_id = generate_ticket_id()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 检查是否有上传的文件
        uploaded_files = []
        if 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                if file and file.filename:
                    import os
                    from werkzeug.utils import secure_filename

                    allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}

                    def allowed_file(filename):
                        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

                    if allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        saved_filename = f"{ticket_id}_{timestamp}_{filename}"

                        upload_dir = os.path.join('static', 'uploads', 'case')
                        os.makedirs(upload_dir, exist_ok=True)

                        file_path = os.path.join(upload_dir, saved_filename)
                        file.save(file_path)
                        uploaded_files.append(saved_filename)

        with db_connection('case') as conn:
            cursor = conn.cursor()
            insert_sql = """
                INSERT INTO tickets (ticket_id, customer_name, customer_contact_name, customer_contact, customer_email,
                                    submit_user, product, issue_type, priority, title, content,
                                    status, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # 客户名称（公司名）：用户填写
            final_customer_name = data['customer_name'].strip()

            # 客户联系人姓名：当前登录用户的真实姓名或用户名
            final_contact_name = data.get('customer_contact_name', user_real_name or user_username).strip()

            # 提交用户名：当前登录用户的用户名
            submit_user = user_username or 'unknown'

            logger.info(f"创建工单 - submit_user: {submit_user}, final_customer_name: {final_customer_name}, final_contact_name: {final_contact_name}")
            logger.info(f"创建工单参数 - ticket_id: {ticket_id}, customer_contact_phone: {data.get('customer_contact_phone')}, customer_email: {customer_email}")

            cursor.execute(insert_sql, (
                ticket_id, final_customer_name, final_contact_name,
                data['customer_contact_phone'].strip(), customer_email, submit_user,
                data['product'].strip(), data['issue_type'].strip(),
                data['priority'].strip(), data['title'].strip(), data['content'].strip(),
                'pending', now, now
            ))

            # 如果有附件，保存到数据库
            if uploaded_files:
                for filename in uploaded_files:
                    file_url = f'/static/uploads/case/{filename}'
                    insert_msg_sql = """
                        INSERT INTO messages (ticket_id, sender, sender_name, content, send_time)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_msg_sql, (
                        ticket_id, 'system', '系统',
                        f'附件上传: {filename}|url:{file_url}', now
                    ))

            conn.commit()
        
        logger.info(f"工单创建成功: {ticket_id}")
        return success_response(data={'ticket_id': ticket_id}, message='工单创建成功')
    except Exception as e:
        log_exception(logger, "工单创建失败")
        return server_error_response(message=f'工单创建失败：{str(e)}')


@case_bp.route('/api/tickets/debug', methods=['GET'])
def debug_tickets():
    """调试接口：检查工单数据"""
    try:
        user_role = session.get('role')
        user_username = session.get('username')

        with db_connection('case') as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # 查询所有工单
            cursor.execute("SELECT ticket_id, customer_name, customer_contact_name, customer_contact, customer_email, submit_user, status, create_time FROM tickets ORDER BY create_time DESC LIMIT 10")
            all_tickets = cursor.fetchall()

            # 查询当前用户相关的工单
            cursor.execute("SELECT COUNT(*) as cnt FROM tickets WHERE submit_user = %s", (user_username,))
            user_ticket_count = cursor.fetchone()

            # 检查 submit_user 字段是否存在
            cursor.execute("SELECT COUNT(*) as cnt FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='casedb' AND TABLE_NAME='tickets' AND COLUMN_NAME='submit_user'")
            submit_user_exists = cursor.fetchone()

            return success_response(data={
                'user_role': user_role,
                'user_username': user_username,
                'submit_user_exists': submit_user_exists,
                'user_ticket_count': user_ticket_count,
                'all_tickets': all_tickets
            }, message='调试信息')
    except Exception as e:
        log_exception(logger, "调试查询失败")
        import traceback
        return server_error_response(message=f'调试失败：{str(e)}\n{traceback.format_exc()}')


@case_bp.route('/api/tickets', methods=['GET'])
def get_tickets():
    """获取工单列表"""
    try:
        log_request(logger, request)
        user_role = session.get('role')
        user_username = session.get('username')
        user_id = session.get('user_id')

        # 添加调试日志
        logger.info(f"工单列表查询 - user_role: {user_role}, user_username: {user_username}, user_id: {user_id}")

        if not user_role:
            return unauthorized_response(message='未登录')

        status = request.args.get('status', '').strip()
        my_only = request.args.get('my_only', 'false').lower() == 'true'

        with db_connection('case') as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # customer 角色: 只能看到自己创建的工单（通过 submit_user 判断）
            if user_role == 'customer':
                if status:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE submit_user = %s AND status = %s ORDER BY create_time DESC
                    """
                    params = (user_username, status)
                    logger.info(f"SQL: {select_sql}, params: {params}")
                    cursor.execute(select_sql, params)
                else:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE submit_user = %s ORDER BY create_time DESC
                    """
                    params = (user_username,)
                    logger.info(f"SQL: {select_sql}, params: {params}")
                    cursor.execute(select_sql, params)
            # admin/user 角色: 可以查看所有工单，支持 my_only 筛选
            elif user_role in ['admin', 'user']:
                if status and my_only:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE status = %s ORDER BY create_time DESC LIMIT 100
                    """
                    cursor.execute(select_sql, (status,))
                elif status:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE status = %s ORDER BY create_time DESC LIMIT 100
                    """
                    cursor.execute(select_sql, (status,))
                else:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets ORDER BY create_time DESC LIMIT 100
                    """
                    cursor.execute(select_sql)
            else:
                tickets = []
                logger.warning(f"未知角色: {user_role}")
                return success_response(data=tickets, message='查询成功')

            tickets = cursor.fetchall()
            logger.info(f"查询到工单数量: {len(tickets)}")
            if tickets:
                logger.info(f"第一个工单: {tickets[0]}")

        for ticket in tickets:
            ticket['create_time'] = ticket['create_time'].strftime('%Y-%m-%d %H:%M:%S')

        return success_response(data=tickets, message='查询成功')
    except Exception as e:
        log_exception(logger, "查询工单列表失败")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return server_error_response(message=f'查询失败：{str(e)}')


@case_bp.route('/api/ticket/<ticket_id>', methods=['GET'])
def get_ticket_detail(ticket_id):
    """获取工单详情"""
    try:
        log_request(logger, request)
        user_role = session.get('role')
        user_username = session.get('username')
        
        if not user_role:
            return unauthorized_response(message='未登录')
        
        with db_connection('case') as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            select_sql = "SELECT * FROM tickets WHERE ticket_id = %s"
            cursor.execute(select_sql, (ticket_id,))
            ticket = cursor.fetchone()
        
        if not ticket:
            from common.response import not_found_response
            return not_found_response(message='工单不存在')

        # customer 角色只能查看自己提交的工单
        if user_role == 'customer' and ticket.get('submit_user') != user_username:
            from common.response import forbidden_response
            return forbidden_response(message='无权访问此工单')
        
        ticket['create_time'] = ticket['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        ticket['update_time'] = ticket['update_time'].strftime('%Y-%m-%d %H:%M:%S')
        ticket['current_user_role'] = user_role
        
        return success_response(data=ticket, message='查询成功')
    except Exception as e:
        log_exception(logger, "查询工单详情失败")
        return server_error_response(message=f'查询失败：{str(e)}')


@case_bp.route('/api/ticket/<ticket_id>/status', methods=['PUT'])
def update_ticket_status(ticket_id):
    """更新工单状态"""
    try:
        log_request(logger, request)
        user_role = session.get('role')
        if not user_role or user_role != 'admin':
            from common.response import forbidden_response
            return forbidden_response(message='无权执行此操作')
        
        data = request.get_json()
        new_status = data.get('status', '').strip()
        
        valid_statuses = ['pending', 'processing', 'completed', 'closed']
        if new_status not in valid_statuses:
            return error_response(message='工单状态值不合法')
        
        with db_connection('case') as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM tickets WHERE ticket_id = %s", (ticket_id,))
            if not cursor.fetchone():
                from common.response import not_found_response
                return not_found_response(message='工单不存在')
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_sql = "UPDATE tickets SET status = %s, update_time = %s WHERE ticket_id = %s"
            cursor.execute(update_sql, (new_status, now, ticket_id))
            conn.commit()

        # 发送 WebSocket 更新通知
        try:
            from services.socketio_service import emit_ticket_update
            emit_ticket_update(ticket_id)
        except ImportError:
            pass

        logger.info(f"工单状态更新: {ticket_id} -> {new_status}")
        return success_response(message='工单状态更新成功')
    except Exception as e:
        log_exception(logger, "更新工单状态失败")
        return server_error_response(message=f'更新失败：{str(e)}')


@case_bp.route('/api/ticket/<ticket_id>/messages', methods=['GET'])
def get_messages(ticket_id):
    """获取工单消息"""
    try:
        log_request(logger, request)

        with db_connection('case') as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            select_sql = """
                SELECT id, ticket_id, sender, sender_name, content, send_time
                FROM messages WHERE ticket_id = %s ORDER BY send_time ASC
            """
            cursor.execute(select_sql, (ticket_id,))
            messages = cursor.fetchall()
        
        for msg in messages:
            msg['send_time'] = msg['send_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return success_response(data=messages, message='查询成功')
    except Exception as e:
        log_exception(logger, "查询工单消息失败")
        return server_error_response(message=f'查询失败：{str(e)}')


@case_bp.route('/submit', methods=['GET'])
def submit_ticket_page():
    """工单提交页面"""
    return render_template('case/submit_ticket.html')


@case_bp.route('/my-tickets', methods=['GET'])
def my_tickets_page():
    """我的工单列表页面"""
    return render_template('case/ticket_list.html')


@case_bp.route('/admin/tickets', methods=['GET'])
def admin_tickets_page():
    """管理员工单列表页面"""
    return render_template('case/ticket_list.html')


@case_bp.route('/ticket/<ticket_id>', methods=['GET'])
def ticket_detail_page(ticket_id):
    """工单详情页面"""
    return render_template('case/ticket_detail.html', ticket_id=ticket_id)


@case_bp.route('/api/ticket/<ticket_id>/message', methods=['POST'])
def send_message(ticket_id):
    """发送消息"""
    try:
        log_request(logger, request)
        
        user_id = session.get('user_id')
        if not user_id:
            return unauthorized_response(message='未登录')
        
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return error_response(message='消息内容不能为空')
        
        sender = session.get('role')
        sender_name = session.get('real_name') or session.get('username', '匿名用户')
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with db_connection('case') as conn:
            cursor = conn.cursor()
            insert_sql = """
                INSERT INTO messages (ticket_id, sender, sender_name, content, send_time)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (ticket_id, sender, sender_name, content, now))
            conn.commit()
        
        logger.info(f"工单 {ticket_id} 新消息: {sender_name}")
        return success_response(message='消息发送成功')
    except Exception as e:
        log_exception(logger, "发送消息失败")
        return server_error_response(message=f'发送失败：{str(e)}')


@case_bp.route('/api/ticket/<ticket_id>/attachment', methods=['POST'])
def upload_attachment(ticket_id):
    """上传附件"""
    try:
        log_request(logger, request)

        user_id = session.get('user_id')
        if not user_id:
            return unauthorized_response(message='未登录')
        
        if 'file' not in request.files:
            return error_response(message='未选择文件')
        
        file = request.files['file']
        if file.filename == '':
            return error_response(message='未选择文件')
        
        import os
        from werkzeug.utils import secure_filename
        
        allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
        
        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
        
        if not allowed_file(file.filename):
            return error_response(message='不支持的文件类型')
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        saved_filename = f"{timestamp}_{filename}"
        
        upload_dir = os.path.join('static', 'uploads', 'case')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, saved_filename)
        file.save(file_path)
        
        logger.info(f"工单 {ticket_id} 附件上传: {saved_filename}")
        return success_response(data={'filename': saved_filename}, message='附件上传成功')
    except Exception as e:
        log_exception(logger, "附件上传失败")
        return server_error_response(message=f'上传失败：{str(e)}')


@case_bp.route('/api/ticket/<ticket_id>/attachments', methods=['GET'])
def get_attachments(ticket_id):
    """获取附件列表"""
    try:
        import os
        
        upload_dir = os.path.join('static', 'uploads', 'case')
        
        if not os.path.exists(upload_dir):
            return success_response(data=[], message='查询成功')
        
        files = []
        for filename in os.listdir(upload_dir):
            if filename.startswith(f"{ticket_id}_"):
                file_path = os.path.join(upload_dir, filename)
                if os.path.isfile(file_path):
                    files.append({
                        'filename': filename,
                        'url': f'/static/uploads/case/{filename}',
                        'size': os.path.getsize(file_path)
                    })
        
        return success_response(data=files, message='查询成功')
    except Exception as e:
        log_exception(logger, "获取附件列表失败")
        return server_error_response(message=f'查询失败：{str(e)}')


@case_bp.route('/api/ticket/<ticket_id>/assign', methods=['POST'])
def assign_ticket(ticket_id):
    """分配工单"""
    try:
        log_request(logger, request)
        
        user_role = session.get('role')
        if not user_role or user_role != 'admin':
            from common.response import forbidden_response
            return forbidden_response(message='无权执行此操作')
        
        data = request.get_json()
        assignee = data.get('assignee', '').strip()
        
        if not assignee:
            return error_response(message='请选择处理人')
        
        with db_connection('case') as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM tickets WHERE ticket_id = %s", (ticket_id,))
            if not cursor.fetchone():
                from common.response import not_found_response
                return not_found_response(message='工单不存在')
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_sql = "UPDATE tickets SET assignee = %s, update_time = %s WHERE ticket_id = %s"
            cursor.execute(update_sql, (assignee, now, ticket_id))
            conn.commit()

        # 发送 WebSocket 更新通知
        try:
            from services.socketio_service import emit_ticket_update
            emit_ticket_update(ticket_id)
        except ImportError:
            pass

        logger.info(f"工单分配: {ticket_id} -> {assignee}")
        return success_response(message='工单分配成功')
    except Exception as e:
        log_exception(logger, "分配工单失败")
        return server_error_response(message=f'分配失败：{str(e)}')


@case_bp.route('/api/ticket/<ticket_id>/close', methods=['POST'])
def close_ticket(ticket_id):
    """关闭工单"""
    try:
        log_request(logger, request)

        user_role = session.get('role')
        if not user_role or user_role != 'admin':
            from common.response import forbidden_response
            return forbidden_response(message='无权执行此操作')
        
        with db_connection('case') as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM tickets WHERE ticket_id = %s", (ticket_id,))
            if not cursor.fetchone():
                from common.response import not_found_response
                return not_found_response(message='工单不存在')
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_sql = "UPDATE tickets SET status = 'closed', update_time = %s WHERE ticket_id = %s"
            cursor.execute(update_sql, (now, ticket_id))
            conn.commit()
        
        logger.info(f"工单关闭: {ticket_id}")
        return success_response(message='工单关闭成功')
    except Exception as e:
        log_exception(logger, "关闭工单失败")
        return server_error_response(message=f'关闭失败：{str(e)}')
