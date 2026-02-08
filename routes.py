"""
统一路由模块 - 整合所有系统的路由
包含：官网、知识库、工单、统一用户管理
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, Response, send_from_directory
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
import re
import hashlib
import uuid
import pymysql
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from werkzeug.security import generate_password_hash, check_password_hash

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from common.db_manager import get_connection
from common.kb_utils import (
    fetch_all_records, fetch_record_by_id, fetch_records_by_name_with_pagination,
    get_total_count, fetch_records_with_pagination, get_kb_db_connection
)
from common.unified_auth import authenticate_user, get_current_user as get_kb_current_user, login_required, create_user, update_user_password


# ==================== 全局变量 ====================
DEBUG_MODE = False

# ==================== 辅助函数 ====================
def get_case_db_connection():
    """获取工单系统数据库连接"""
    return get_connection('case')

def get_kb_conn():
    """获取知识库数据库连接"""
    return get_kb_db_connection()

def get_unified_kb_conn():
    """获取知识库数据库连接（用于统一用户管理）"""
    return get_connection('kb')

def is_valid_email(email):
    """校验邮箱格式是否合法"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def generate_ticket_id():
    """生成唯一工单ID"""
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = str(uuid.uuid4())[:6].upper()
    return f"TK-{now}-{random_str}"

def get_db_cursor():
    """获取工单数据库游标"""
    conn = get_case_db_connection()
    if not conn:
        return None
    return conn.cursor(pymysql.cursors.DictCursor)


# ==================== 路由注册函数 ====================
def register_all_routes(app):
    """注册所有路由到Flask应用"""

    # favicon路由
    @app.route('/favicon.ico')
    def favicon():
        return Response('', mimetype='image/x-icon')

    # 官网静态文件路由 (兼容 /jpg/ 路径)
    @app.route('/jpg/<path:filename>')
    def serve_jpg_static(filename):
        """提供官网静态文件"""
        try:
            return send_from_directory(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'home', 'images'),
                filename
            )
        except:
            return "404 - File Not Found", 404

    # 404错误处理
    @app.errorhandler(404)
    def not_found(error):
        if error:
            return "404 - Page Not Found", 404
        return redirect(url_for('home_index'))

    # 500错误处理
    @app.errorhandler(500)
    def internal_error(error):
        return "500 - Internal Server Error", 500

    # 会话管理中间件
    @app.before_request
    def before_request():
        session.permanent = False

    # ==================== 官网系统路由 ====================

    @app.route('/')
    def home_index():
        """首页"""
        return render_template('home_index.html', now=datetime.now())

    @app.route('/test-images')
    def test_images():
        """图片测试页面"""
        return render_template('home_test_images.html')

    @app.route('/view-messages')
    def view_messages():
        """留言管理页面"""
        return render_template('home_admin_messages.html')

    @app.route('/api/contact', methods=['POST'])
    def contact():
        """联系表单提交"""
        try:
            data = request.get_json()
            if not data.get('name'):
                return jsonify({'success': False, 'message': '请填写姓名'}), 400
            if not data.get('email'):
                return jsonify({'success': False, 'message': '请填写邮箱'}), 400
            if not data.get('message'):
                return jsonify({'success': False, 'message': '请填写留言内容'}), 400
            return jsonify({'success': True, 'message': '留言提交成功'}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': f'提交失败：{str(e)}'}), 500

    @app.route('/api/messages', methods=['GET'])
    def get_messages():
        """获取留言列表"""
        return jsonify({'success': True, 'messages': []})

    @app.route('/messages')
    def messages():
        """留言管理"""
        return render_template('home_admin_messages.html')

    @app.route('/dashboard')
    def dashboard():
        """管理仪表板"""
        return render_template('home_admin_dashboard.html')

    # ==================== 知识库系统路由 ====================

    # 认证路由
    @app.route('/kb/auth/login', methods=['GET', 'POST'])
    def kb_login():
        """登录页面"""
        if get_kb_current_user():
            return redirect(url_for('kb_index'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            if not username or not password:
                return render_template('kb_login.html', error="请输入用户名和密码")

            success, result = authenticate_user(username, password)

            if success:
                user_info = result
                session['user_id'] = user_info['id']
                session['username'] = user_info['username']
                session['display_name'] = user_info['display_name']
                session['role'] = user_info['role']
                session['login_time'] = datetime.now().isoformat()
                session.permanent = False

                next_url = request.form.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(url_for('kb_index'))
            else:
                return render_template('kb_login.html', error=result, username=username)

        return render_template('kb_login.html')

    @app.route('/kb/auth/logout')
    def kb_logout():
        """退出登录"""
        session.clear()
        return redirect(url_for('kb_login'))

    @app.route('/kb/auth/check-login')
    def kb_check_login():
        """检查登录状态"""
        user = get_kb_current_user()
        if user:
            return jsonify({'success': True, 'user': user})
        return jsonify({'success': False})

    # 兼容旧的路由路径
    @app.route('/auth/check-login')
    def auth_check_login():
        """检查登录状态 - 兼容路由"""
        user = get_kb_current_user()
        if user:
            return jsonify({'success': True, 'user': user})
        return jsonify({'success': False})

    # 兼容旧的登录路由
    @app.route('/auth/login')
    def auth_login():
        """登录页面 - 兼容路由"""
        return redirect(url_for('kb_login'))

    @app.route('/auth/logout')
    def auth_logout():
        """退出登录 - 兼容路由"""
        return redirect(url_for('kb_logout'))

    # 兼容旧的 /debug 路由
    @app.route('/debug')
    def debug_redirect():
        """调试页面 - 重定向到知识库管理页面的调试功能"""
        return redirect(url_for('kb_management'))

    # 修改密码页面路由
    @app.route('/kb/auth/change-password')
    @login_required()
    def kb_change_password_page():
        """修改密码页面"""
        return render_template('kb_change_password.html')

    # 修改密码API路由
    @app.route('/auth/api/change-password', methods=['POST'])
    def change_password():
        """修改当前用户密码"""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'message': '未登录'}), 401

            data = request.get_json()
            old_password = data.get('old_password', '').strip()
            new_password = data.get('new_password', '').strip()

            if not old_password or not new_password:
                return jsonify({'success': False, 'message': '请输入旧密码和新密码'}), 400

            if len(new_password) < 6:
                return jsonify({'success': False, 'message': '新密码长度至少为6位'}), 400

            # 验证旧密码
            username = session.get('username')
            success, result = authenticate_user(username, old_password)

            if not success:
                return jsonify({'success': False, 'message': '旧密码错误'}), 400

            # 更新密码（统一使用werkzeug）
            success, message = update_user_password(user_id, new_password)

            if success:
                return jsonify({'success': True, 'message': '密码修改成功'})
            else:
                return jsonify({'success': False, 'message': message}), 500

        except Exception as e:
            return jsonify({'success': False, 'message': f'修改密码失败：{str(e)}'}), 500

    # Trilium 搜索路由
    @app.route('/api/trilium/search')
    def trilium_search():
        """Trilium 搜索"""
        try:
            query = request.args.get('q', '').strip()
            limit = int(request.args.get('limit', 30))

            if not query:
                return jsonify({'success': False, 'message': '请输入搜索关键词'}), 400

            # 检查 Trilium 配置
            if not hasattr(config, 'TRILIUM_SERVER_URL') or not config.TRILIUM_SERVER_URL:
                return jsonify({'success': False, 'message': 'Trilium 服务未配置'}), 500

            # 模拟搜索结果 (实际需要调用 Trilium API)
            # TODO: 实现真实的 Trilium 搜索调用
            results = []
            return jsonify({
                'success': True,
                'results': results,
                'query': query,
                'count': len(results)
            })

        except Exception as e:
            return jsonify({'success': False, 'message': f'搜索失败：{str(e)}'}), 500

    # Trilium 内容加载路由
    @app.route('/api/trilium/content')
    def trilium_content():
        """获取 Trilium 笔记内容"""
        try:
            kb_number = request.args.get('kb_number', '').strip()
            trilium_url = request.args.get('trilium_url', '').strip()

            if not trilium_url:
                return jsonify({'success': False, 'message': '缺少 Trilium URL 参数'}), 400

            # 构建完整的 Trilium URL
            if not trilium_url.startswith('http'):
                if hasattr(config, 'TRILIUM_SERVER_URL') and config.TRILIUM_SERVER_URL:
                    base_url = config.TRILIUM_SERVER_URL.rstrip('/')
                    trilium_url = f"{base_url}/{trilium_url}"
                else:
                    return jsonify({'success': False, 'message': 'Trilium 服务未配置'}), 500

            # 检查 Trilium Token 配置
            if not hasattr(config, 'TRILIUM_TOKEN') or not config.TRILIUM_TOKEN:
                return jsonify({'success': False, 'message': 'Trilium 认证未配置'}), 500

            # 模拟内容加载 (实际需要调用 Trilium API 获取笔记内容)
            # TODO: 实现真实的 Trilium 内容获取
            return jsonify({
                'success': False,
                'message': 'Trilium 内容集成功能开发中，暂时无法显示内容。您可以直接点击"在Trilium中打开"查看。',
                'content': '',
                'url': trilium_url
            })

        except Exception as e:
            return jsonify({'success': False, 'message': f'加载内容失败：{str(e)}'}), 500

    # 知识库主页
    @app.route('/kb/')
    def kb_index():
        """知识库首页"""
        user = get_kb_current_user()
        if not user:
            return redirect(url_for('kb_login', next=request.url))

        try:
            page = request.args.get('page', 1, type=int)
            per_page = 15
            records, total_count = fetch_records_with_pagination(page, per_page)
            total_pages = (total_count + per_page - 1) // per_page
            showing_start = (page - 1) * per_page + 1
            showing_end = min(page * per_page, total_count)

            return render_template('kb_index.html',
                                 records=records,
                                 total_count=total_count,
                                 showing_count=showing_end - showing_start + 1 if records else 0,
                                 page=page,
                                 per_page=per_page,
                                 total_pages=total_pages,
                                 showing_start=showing_start,
                                 showing_end=showing_end,
                                 is_search=False,
                                 trilium_base_url=config.TRILIUM_SERVER_URL,
                                 current_user=user)
        except Exception as e:
            error_msg = f"数据库连接错误: {str(e)}"
            return render_template('kb_index.html',
                                 records=[],
                                 error=error_msg,
                                 total_count=0,
                                 showing_count=0,
                                 page=1,
                                 per_page=15,
                                 total_pages=1,
                                 is_search=False,
                                 current_user=user)

    @app.route('/kb/search', methods=['GET'])
    def kb_search():
        """搜索"""
        search_id = request.args.get('id', '').strip()
        page = request.args.get('page', 1, type=int)

        if not search_id:
            return render_template('kb_index.html',
                                 records=[],
                                 error="请输入搜索ID",
                                 total_count=get_total_count(),
                                 showing_count=0,
                                 page=1,
                                 per_page=15,
                                 total_pages=1,
                                 is_search=True,
                                 search_id="")

        try:
            record_id = int(search_id)
            record = fetch_record_by_id(record_id)

            if record:
                return render_template('kb_index.html',
                                     records=[record],
                                     total_count=1,
                                     showing_count=1,
                                     page=page,
                                     per_page=15,
                                     total_pages=1,
                                     search_id=search_id,
                                     is_search=True)
            else:
                return render_template('kb_index.html',
                                     records=[],
                                     error=f"未找到ID为 {search_id} 的记录",
                                     total_count=get_total_count(),
                                     showing_count=0,
                                     page=1,
                                     per_page=15,
                                     total_pages=1,
                                     search_id=search_id,
                                     is_search=True)
        except ValueError:
            return render_template('kb_index.html',
                                 records=[],
                                 error="请输入有效的数字ID",
                                 total_count=get_total_count(),
                                 showing_count=0,
                                 page=1,
                                 per_page=15,
                                 total_pages=1,
                                 search_id=search_id,
                                 is_search=True)

    # 兼容旧的路由 /search (重定向到 /kb/search)
    @app.route('/search', methods=['GET'])
    def old_kb_search():
        """旧搜索路由 - 重定向到新路由"""
        return redirect(url_for('kb_search', **request.args))

    @app.route('/kb/api/all')
    def kb_get_all():
        """获取所有数据"""
        try:
            records = fetch_all_records()
            return jsonify({'success': True, 'records': records, 'count': len(records)})
        except Exception as e:
            return jsonify({'success': False, 'message': f"数据库错误: {str(e)}"})

    @app.route('/kb/search/name', methods=['POST'])
    def kb_search_by_name():
        """按名称搜索"""
        name = request.form.get('name', '').strip()
        page = request.form.get('page', 1, type=int)
        per_page = request.form.get('per_page', 15, type=int)

        if not name:
            return jsonify({'success': False, 'message': '请输入知识库名称'})

        try:
            records, total_count = fetch_records_by_name_with_pagination(name, page, per_page)
            total_pages = (total_count + per_page - 1) // per_page
            return jsonify({
                'success': True,
                'records': records,
                'count': len(records),
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f"搜索错误: {str(e)}"})

    @app.route('/kb/api/stats')
    def kb_get_stats():
        """统计信息"""
        try:
            count = get_total_count()
            return jsonify({'success': True, 'total_count': count})
        except Exception as e:
            return jsonify({'success': False, 'message': f"统计信息获取失败: {str(e)}"})

    # 知识库管理路由
    @app.route('/kb/MGMT/')
    @login_required(roles=['admin'])
    def kb_management():
        """管理页面 - 使用分页加载优化性能"""
        try:
            # 使用分页加载第一页数据，而非加载所有记录
            page = request.args.get('page', 1, type=int)
            per_page = 20  # 每页显示20条记录
            records, total_count = fetch_records_with_pagination(page, per_page)
            user = get_kb_current_user()

            total_pages = (total_count + per_page - 1) // per_page
            showing_start = (page - 1) * per_page + 1
            showing_end = min(page * per_page, total_count)

            return render_template('kb_management.html',
                                 records=records,
                                 total_count=total_count,
                                 showing_count=showing_end - showing_start + 1 if records else 0,
                                 page=page,
                                 per_page=per_page,
                                 total_pages=total_pages,
                                 showing_start=showing_start,
                                 showing_end=showing_end,
                                 current_user=user,
                                 debug_mode=DEBUG_MODE)
        except Exception as e:
            return render_template('kb_management.html',
                                 records=[],
                                 error=str(e),
                                 total_count=0,
                                 page=1,
                                 per_page=20,
                                 total_pages=1)

    # 知识库用户管理路由
    @app.route('/kb/auth/users')
    @login_required(roles=['admin'])
    def kb_user_management():
        """用户管理页面"""
        try:
            conn = get_unified_kb_conn()
            if not conn:
                return render_template('kb_user_management.html',
                                     users=[],
                                     login_logs=[],
                                     error='数据库连接失败')

            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # 获取用户列表
            cursor.execute("SELECT * FROM `users` ORDER BY created_at DESC")
            users = cursor.fetchall()

            # 获取最近登录日志
            cursor.execute("""
                SELECT l.*, u.username, u.display_name
                FROM mgmt_login_logs l
                LEFT JOIN `users` u ON l.user_id = u.id
                ORDER BY l.login_time DESC
                LIMIT 20
            """)
            login_logs = cursor.fetchall()

            cursor.close()
            conn.close()

            return render_template('kb_user_management.html',
                                 users=users,
                                 login_logs=login_logs,
                                 total_count=len(users) if users else 0)
        except Exception as e:
            return render_template('kb_user_management.html',
                                 users=[],
                                 login_logs=[],
                                 error=str(e),
                                 total_count=0)

    # 兼容旧的用户管理路由
    @app.route('/auth/users')
    @login_required(roles=['admin'])
    def auth_user_management():
        """用户管理页面 - 兼容路由"""
        return redirect(url_for('kb_user_management'))

    # 知识库用户管理API（兼容旧路由）
    @app.route('/auth/api/add-user', methods=['POST'])
    @login_required(roles=['admin'])
    def kb_add_user():
        """添加知识库用户"""
        try:
            data = request.get_json()

            if not data.get('username'):
                return jsonify({'success': False, 'message': '用户名不能为空'}), 400
            if not data.get('password'):
                return jsonify({'success': False, 'message': '密码不能为空'}), 400

            # 使用统一用户创建接口
            success, message = create_user(
                username=data['username'],
                password=data['password'],
                display_name=data.get('display_name', ''),
                email=data.get('email', ''),
                role=data.get('role', 'user'),
                created_by=session.get('username', 'admin')
            )

            if success:
                return jsonify({'success': True, 'message': message})
            else:
                return jsonify({'success': False, 'message': message}), 400
        except Exception as e:
            return jsonify({'success': False, 'message': f'添加用户失败：{str(e)}'}), 500

    @app.route('/auth/api/update-user/<int:user_id>', methods=['PUT'])
    @login_required(roles=['admin'])
    def kb_update_user(user_id):
        """更新知识库用户"""
        try:
            data = request.get_json()

            conn = get_unified_kb_conn()
            if not conn:
                return jsonify({'success': False, 'message': '数据库连接失败'}), 500

            cursor = conn.cursor()

            # 构建更新SQL
            update_fields = []
            update_values = []

            if data.get('display_name') is not None:
                update_fields.append('display_name = %s')
                update_values.append(data['display_name'])

            if data.get('real_name') is not None:
                update_fields.append('real_name = %s')
                update_values.append(data['real_name'])

            if data.get('role'):
                update_fields.append('role = %s')
                update_values.append(data['role'])

            if data.get('status'):
                update_fields.append('status = %s')
                update_values.append(data['status'])

            if data.get('email') is not None:
                update_fields.append('email = %s')
                update_values.append(data['email'])

            if data.get('password'):
                # 生成新的 werkzeug 密码哈希
                password_hash = generate_password_hash(data['password'])
                update_fields.append('password_hash = %s')
                update_values.append(password_hash)
                update_fields.append('password_type = %s')
                update_values.append('werkzeug')

            update_values.append(user_id)

            if update_fields:
                sql = f"UPDATE `users` SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(sql, update_values)
                conn.commit()

            cursor.close()
            conn.close()

            return jsonify({'success': True, 'message': '用户更新成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'更新用户失败：{str(e)}'}), 500

    @app.route('/auth/api/delete-user/<int:user_id>', methods=['DELETE'])
    @login_required(roles=['admin'])
    def kb_delete_user(user_id):
        """删除知识库用户"""
        try:
            conn = get_unified_kb_conn()
            if not conn:
                return jsonify({'success': False, 'message': '数据库连接失败'}), 500

            cursor = conn.cursor()

            # 检查是否是admin用户
            cursor.execute("SELECT username FROM `users` WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user and user[0] == 'admin':
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '不能删除admin用户'}), 400

            cursor.execute("DELETE FROM `users` WHERE id = %s", (user_id,))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({'success': True, 'message': '用户删除成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'删除用户失败：{str(e)}'}), 500

    @app.route('/kb/MGMT/api/add', methods=['POST'])
    @login_required(roles=['admin'])
    def kb_add_record():
        """添加记录"""
        try:
            data = request.get_json()

            if not data.get('KB_Number'):
                return jsonify({'success': False, 'message': '知识库编号不能为空'})
            if not data.get('KB_Name'):
                return jsonify({'success': False, 'message': '知识库名称不能为空'})

            existing = fetch_record_by_id(data['KB_Number'])
            if existing:
                return jsonify({'success': False, 'message': f"编号 {data['KB_Number']} 已存在"})

            connection = get_kb_conn()
            if connection is None:
                return jsonify({'success': False, 'message': '数据库连接失败'})

            with connection.cursor() as cursor:
                sql = "INSERT INTO `KB-info` (KB_Number, KB_Name, KB_link) VALUES (%s, %s, %s)"
                cursor.execute(sql, (data['KB_Number'], data['KB_Name'], data.get('KB_link', '')))
                connection.commit()
                affected_rows = cursor.rowcount

            connection.close()

            if affected_rows > 0:
                return jsonify({'success': True, 'message': '记录添加成功', 'id': data['KB_Number']})
            else:
                return jsonify({'success': False, 'message': '添加记录失败'})
        except Exception as e:
            return jsonify({'success': False, 'message': f"添加记录时发生错误: {str(e)}"})

    @app.route('/kb/MGMT/api/update/<int:record_id>', methods=['PUT'])
    @login_required(roles=['admin'])
    def kb_update_record(record_id):
        """更新记录"""
        try:
            data = request.get_json()
            existing = fetch_record_by_id(record_id)
            if not existing:
                return jsonify({'success': False, 'message': f"记录 {record_id} 不存在"})

            connection = get_kb_conn()
            if connection is None:
                return jsonify({'success': False, 'message': '数据库连接失败'})

            with connection.cursor() as cursor:
                sql = "UPDATE `KB-info` SET KB_Name = %s, KB_link = %s WHERE KB_Number = %s"
                cursor.execute(sql, (data.get('KB_Name', existing['KB_Name']), data.get('KB_link', existing['KB_link']), record_id))
                connection.commit()
                affected_rows = cursor.rowcount

            connection.close()

            if affected_rows > 0:
                return jsonify({'success': True, 'message': '记录更新成功'})
            else:
                return jsonify({'success': False, 'message': '更新记录失败'})
        except Exception as e:
            return jsonify({'success': False, 'message': f"更新记录时发生错误: {str(e)}"})

    @app.route('/kb/MGMT/api/delete/<int:record_id>', methods=['DELETE'])
    @login_required(roles=['admin'])
    def kb_delete_record(record_id):
        """删除记录"""
        try:
            existing = fetch_record_by_id(record_id)
            if not existing:
                return jsonify({'success': False, 'message': f"记录 {record_id} 不存在"})

            connection = get_kb_conn()
            if connection is None:
                return jsonify({'success': False, 'message': '数据库连接失败'})

            with connection.cursor() as cursor:
                sql = "DELETE FROM `KB-info` WHERE KB_Number = %s"
                cursor.execute(sql, (record_id,))
                connection.commit()
                affected_rows = cursor.rowcount

            connection.close()

            if affected_rows > 0:
                return jsonify({'success': True, 'message': '记录删除成功'})
            else:
                return jsonify({'success': False, 'message': '删除记录失败'})
        except Exception as e:
            return jsonify({'success': False, 'message': f"删除记录时发生错误: {str(e)}"})

    # 批量添加记录API
    @app.route('/kb/MGMT/api/batch-add', methods=['POST'])
    @login_required(roles=['admin'])
    def kb_batch_add_record():
        """批量添加记录"""
        try:
            data = request.get_json()
            records = data.get('records', [])

            if not records:
                return jsonify({'success': False, 'message': '没有要添加的记录'})

            connection = get_kb_conn()
            if connection is None:
                return jsonify({'success': False, 'message': '数据库连接失败'})

            success_count = 0
            duplicate_count = 0
            failed_count = 0
            failed_records = []

            with connection.cursor() as cursor:
                for record in records:
                    try:
                        # 检查是否已存在
                        cursor.execute("SELECT KB_Number FROM `KB-info` WHERE KB_Number = %s", (record.get('KB_Number'),))
                        if cursor.fetchone():
                            duplicate_count += 1
                            failed_records.append({
                                'record': record,
                                'reason': '编号已存在'
                            })
                            continue

                        # 插入记录
                        sql = "INSERT INTO `KB-info` (KB_Number, KB_Name, KB_link) VALUES (%s, %s, %s)"
                        cursor.execute(sql, (record.get('KB_Number'), record.get('KB_Name'), record.get('KB_link', '')))
                        success_count += 1
                    except Exception as e:
                        failed_count += 1
                        failed_records.append({
                            'record': record,
                            'reason': str(e)
                        })

                connection.commit()

            connection.close()

            return jsonify({
                'success': True,
                'message': f'批量添加完成：成功 {success_count} 条，跳过重复 {duplicate_count} 条，失败 {failed_count} 条',
                'summary': {
                    'total': len(records),
                    'success': success_count,
                    'duplicate': duplicate_count,
                    'failed': failed_count
                },
                'failed_records': failed_records
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f"批量添加记录时发生错误: {str(e)}"})

    # 批量删除记录API
    @app.route('/kb/MGMT/api/batch-delete', methods=['POST'])
    @login_required(roles=['admin'])
    def kb_batch_delete_records():
        """批量删除记录"""
        try:
            data = request.get_json()
            ids = data.get('ids', [])

            if not ids:
                return jsonify({'success': False, 'message': '没有要删除的记录'})

            connection = get_kb_conn()
            if connection is None:
                return jsonify({'success': False, 'message': '数据库连接失败'})

            with connection.cursor() as cursor:
                placeholders = ','.join(['%s'] * len(ids))
                sql = f"DELETE FROM `KB-info` WHERE KB_Number IN ({placeholders})"
                cursor.execute(sql, ids)
                affected_rows = cursor.rowcount
                connection.commit()

            connection.close()

            return jsonify({
                'success': True,
                'message': f'成功删除 {affected_rows} 条记录'
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f"批量删除记录时发生错误: {str(e)}"})

    # 导出数据API
    @app.route('/kb/MGMT/api/export', methods=['GET'])
    @login_required(roles=['admin'])
    def kb_export_data():
        """导出所有数据"""
        try:
            records = fetch_all_records()
            return jsonify({
                'success': True,
                'message': '数据导出成功',
                'data': records,
                'count': len(records)
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f"导出数据时发生错误: {str(e)}"})

    # 分页加载记录API
    @app.route('/kb/MGMT/api/records', methods=['GET'])
    @login_required(roles=['admin'])
    def kb_get_paginated_records():
        """获取分页记录"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            search_name = request.args.get('search', '').strip()

            if not page or page < 1:
                page = 1
            if not per_page or per_page < 1 or per_page > 100:
                per_page = 20

            if search_name:
                records, total_count = fetch_records_by_name_with_pagination(search_name, page, per_page)
            else:
                records, total_count = fetch_records_with_pagination(page, per_page)

            total_pages = (total_count + per_page - 1) // per_page
            showing_start = (page - 1) * per_page + 1
            showing_end = min(page * per_page, total_count)

            return jsonify({
                'success': True,
                'records': records,
                'total_count': total_count,
                'showing_count': showing_end - showing_start + 1 if records else 0,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'showing_start': showing_start,
                'showing_end': showing_end
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f"获取记录失败: {str(e)}",
                'records': [],
                'total_count': 0,
                'total_pages': 1,
                'page': 1
            })

    # 系统状态API
    @app.route('/kb/MGMT/api/system-status', methods=['GET'])
    @login_required(roles=['admin'])
    def kb_system_status():
        """获取系统状态"""
        try:
            from datetime import datetime

            # 只获取记录总数，不加载所有记录
            total_records = get_total_count()

            # 获取用户数量和最新记录时间
            conn = get_unified_kb_conn()
            user_count = 0
            latest_record_time = None
            database_connected = True

            if conn:
                try:
                    cursor = conn.cursor(pymysql.cursors.DictCursor)
                    cursor.execute("SELECT COUNT(*) as count FROM `users`")
                    user_count = cursor.fetchone()['count']

                    # 获取最新记录时间（仅在必要时）
                    if total_records > 0:
                        cursor.execute("SELECT MAX(KB_UpdateTime) as max_time FROM `KB-info`")
                        result = cursor.fetchone()
                        if result and result.get('max_time'):
                            latest_record_time = result['max_time'].strftime('%Y-%m-%d %H:%M:%S')

                    cursor.close()
                except Exception as e:
                    database_connected = False
                finally:
                    conn.close()

            # 确定系统健康状态
            if not database_connected:
                system_health = 'database_error'
            elif total_records == 0:
                system_health = 'connected_no_data'
            else:
                system_health = 'healthy'

            return jsonify({
                'success': True,
                'system_health': system_health,
                'database_connected': database_connected,
                'total_records': total_records,
                'user_count': user_count,
                'latest_record_time': latest_record_time,
                'current_user': get_kb_current_user(),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f"获取系统状态失败: {str(e)}"
            })

    # 切换调试模式API
    @app.route('/kb/MGMT/api/toggle-debug', methods=['POST'])
    @login_required(roles=['admin'])
    def kb_toggle_debug():
        """切换调试模式"""
        try:
            data = request.get_json()
            debug_mode = data.get('debug_mode', False)

            global DEBUG_MODE
            DEBUG_MODE = debug_mode

            return jsonify({
                'success': True,
                'message': f'调试模式已{"开启" if debug_mode else "关闭"}',
                'debug_mode': debug_mode
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f"切换调试模式失败: {str(e)}"})

    # 获取调试信息API
    @app.route('/kb/MGMT/debug', methods=['GET'])
    @login_required(roles=['admin'])
    def kb_debug_info():
        """获取调试信息"""
        try:
            from datetime import datetime

            # 收集系统信息
            debug_data = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'debug_mode': DEBUG_MODE,
                    'python_version': sys.version,
                    'flask_version': request.environ.get('FLASK_VERSION', 'unknown')
                },
                'database': {
                    'kb_database': config.DB_NAME_KB,
                    'case_database': config.DB_NAME_CASE,
                    'home_database': config.DB_NAME_HOME
                },
                'current_user': get_kb_current_user(),
                'config': {
                    'trilium_server': config.TRILIUM_SERVER_URL if hasattr(config, 'TRILIUM_SERVER_URL') else None,
                    'trilium_token': '***hidden***' if config.TRILIUM_TOKEN else None,
                    'session_timeout': config.SESSION_TIMEOUT if hasattr(config, 'SESSION_TIMEOUT') else None
                },
                'request': {
                    'method': request.method,
                    'url': request.url,
                    'path': request.path,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent')
                }
            }

            # 获取数据库统计
            try:
                # 只获取记录总数，不加载所有记录
                debug_data['database']['kb_records_count'] = get_total_count()

                conn = get_unified_kb_conn()
                if conn:
                    try:
                        cursor = conn.cursor(pymysql.cursors.DictCursor)

                        # 用户统计
                        cursor.execute("SELECT COUNT(*) as count FROM `users`")
                        debug_data['database']['user_count'] = cursor.fetchone()['count']

                        # 最近登录
                        cursor.execute("""
                            SELECT username, last_login FROM `users`
                            WHERE last_login IS NOT NULL
                            ORDER BY last_login DESC LIMIT 5
                        """)
                        debug_data['database']['recent_logins'] = cursor.fetchall()

                        cursor.close()
                    except Exception as e:
                        debug_data['database']['error'] = str(e)
                    finally:
                        conn.close()
            except Exception as e:
                debug_data['database']['error'] = str(e)

            return jsonify({
                'success': True,
                'data': debug_data
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f"获取调试信息失败: {str(e)}"
            })

    # 系统清理API
    @app.route('/kb/MGMT/api/cleanup', methods=['POST'])
    @login_required(roles=['admin'])
    def kb_system_cleanup():
        """系统清理"""
        try:
            # 这里可以添加清理逻辑，比如清理临时文件、旧日志等
            return jsonify({
                'success': True,
                'message': '系统清理完成'
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f"系统清理失败: {str(e)}"})


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
                return jsonify({'code': 400, 'msg': '用户名和密码不能为空'}), 400

            # 使用统一认证
            success, result = authenticate_user(username, password)

            if not success:
                return jsonify({'code': 401, 'msg': result}), 401

            user_info = result

            session['user_id'] = user_info['id']
            session['username'] = user_info['username']
            session['real_name'] = user_info.get('real_name') or user_info.get('display_name', '')
            session['role'] = user_info['role']
            session['display_name'] = user_info.get('display_name', '')

            return jsonify({
                'code': 200,
                'msg': '登录成功',
                'data': {
                    'user_id': user_info['id'],
                    'username': user_info['username'],
                    'real_name': user_info.get('real_name') or user_info.get('display_name', ''),
                    'role': user_info['role']
                }
            })
        except Exception as e:
            return jsonify({'code': 500, 'msg': f'登录失败：{str(e)}'}), 500

    @app.route('/case/api/logout', methods=['POST'])
    def case_logout():
        """登出"""
        session.clear()
        return jsonify({'code': 200, 'msg': '登出成功'})

    @app.route('/case/api/user/info', methods=['GET'])
    def case_get_user_info():
        """获取用户信息"""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'code': 401, 'msg': '未登录'}), 401

        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'user_id': session.get('user_id'),
                'username': session.get('username'),
                'real_name': session.get('real_name'),
                'role': session.get('role'),
                'email': session.get('email')
            }
        })

    @app.route('/case/api/ticket', methods=['POST'])
    def case_create_ticket():
        """创建工单"""
        try:
            data = request.get_json()
            required_fields = [
                'customer_name', 'customer_contact', 'customer_email',
                'product', 'issue_type', 'priority', 'title', 'content'
            ]

            for field in required_fields:
                if field not in data or not str(data[field]).strip():
                    return jsonify({'code': 400, 'msg': f'缺少必填字段：{field}或字段值为空'}), 400

            customer_email = data['customer_email'].strip()
            if not is_valid_email(customer_email):
                return jsonify({'code': 400, 'msg': '客户邮箱格式不合法'}), 400

            valid_issue_types = ['technical', 'service', 'complaint', 'other']
            valid_priorities = ['low', 'medium', 'high', 'urgent']
            if data['issue_type'].strip() not in valid_issue_types:
                return jsonify({'code': 400, 'msg': '问题类型值不合法'}), 400
            if data['priority'].strip() not in valid_priorities:
                return jsonify({'code': 400, 'msg': '优先级值不合法'}), 400

            ticket_id = generate_ticket_id()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            conn = get_case_db_connection()
            if not conn:
                return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
            cursor = conn.cursor()
            insert_sql = """
                INSERT INTO tickets (ticket_id, customer_name, customer_contact, customer_email,
                                    product, issue_type, priority, title, content,
                                    status, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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

            return jsonify({'code': 200, 'msg': '工单创建成功', 'data': {'ticket_id': ticket_id}})
        except Exception as e:
            return jsonify({'code': 500, 'msg': f'工单创建失败：{str(e)}'}), 500

    @app.route('/case/api/tickets', methods=['GET'])
    def case_get_tickets():
        """获取工单列表"""
        try:
            user_role = session.get('role')
            user_username = session.get('username')

            if not user_role:
                return jsonify({'code': 401, 'msg': '未登录'}), 401

            status = request.args.get('status', '').strip()
            conn = get_case_db_connection()
            if not conn:
                return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
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
                return jsonify({'code': 200, 'msg': '查询成功', 'data': tickets})

            tickets = cursor.fetchall()
            cursor.close()
            conn.close()

            for ticket in tickets:
                ticket['create_time'] = ticket['create_time'].strftime('%Y-%m-%d %H:%M:%S')

            return jsonify({'code': 200, 'msg': '查询成功', 'data': tickets})
        except Exception as e:
            return jsonify({'code': 500, 'msg': f'查询失败：{str(e)}'}), 500

    @app.route('/case/api/ticket/<ticket_id>', methods=['GET'])
    def case_get_ticket_detail(ticket_id):
        """获取工单详情"""
        try:
            user_role = session.get('role')
            user_username = session.get('username')

            if not user_role:
                return jsonify({'code': 401, 'msg': '未登录'}), 401

            conn = get_case_db_connection()
            if not conn:
                return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            select_sql = "SELECT * FROM tickets WHERE ticket_id = %s"
            cursor.execute(select_sql, (ticket_id,))
            ticket = cursor.fetchone()
            cursor.close()
            conn.close()

            if not ticket:
                return jsonify({'code': 404, 'msg': '工单不存在'}), 404

            if user_role == 'customer' and ticket['customer_name'] != user_username:
                return jsonify({'code': 403, 'msg': '无权访问此工单'}), 403

            ticket['create_time'] = ticket['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            ticket['update_time'] = ticket['update_time'].strftime('%Y-%m-%d %H:%M:%S')
            ticket['current_user_role'] = user_role

            return jsonify({'code': 200, 'msg': '查询成功', 'data': ticket})
        except Exception as e:
            return jsonify({'code': 500, 'msg': f'查询失败：{str(e)}'}), 500

    @app.route('/case/api/ticket/<ticket_id>/status', methods=['PUT'])
    def case_update_ticket_status(ticket_id):
        """更新工单状态"""
        try:
            user_role = session.get('role')
            if not user_role or user_role != 'admin':
                return jsonify({'code': 403, 'msg': '无权执行此操作'}), 403

            data = request.get_json()
            new_status = data.get('status', '').strip()

            valid_statuses = ['pending', 'processing', 'completed', 'closed']
            if new_status not in valid_statuses:
                return jsonify({'code': 400, 'msg': '工单状态值不合法'}), 400

            conn = get_case_db_connection()
            if not conn:
                return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM tickets WHERE ticket_id = %s", (ticket_id,))
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'code': 404, 'msg': '工单不存在'}), 404

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_sql = "UPDATE tickets SET status = %s, update_time = %s WHERE ticket_id = %s"
            cursor.execute(update_sql, (new_status, now, ticket_id))
            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({'code': 200, 'msg': '工单状态更新成功'})
        except Exception as e:
            return jsonify({'code': 500, 'msg': f'更新失败：{str(e)}'}), 500

    @app.route('/case/api/ticket/<ticket_id>/messages', methods=['GET'])
    def case_get_messages(ticket_id):
        """获取工单消息"""
        try:
            conn = get_case_db_connection()
            if not conn:
                return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
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

            return jsonify({'code': 200, 'msg': '查询成功', 'data': messages})
        except Exception as e:
            return jsonify({'code': 500, 'msg': f'查询失败：{str(e)}'}), 500

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
                return jsonify({'success': False, 'message': '数据库连接失败'}), 500

            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM `users` ORDER BY created_at DESC")
            users = cursor.fetchall()
            cursor.close()
            conn.close()

            return jsonify({'success': True, 'data': users})
        except Exception as e:
            return jsonify({'success': False, 'message': f'获取用户列表失败：{str(e)}'}), 500

    @app.route('/unified/api/users', methods=['POST'])
    @login_required(roles=['admin'])
    def unified_add_user():
        """添加统一用户"""
        try:
            data = request.get_json()

            if not data.get('username'):
                return jsonify({'success': False, 'message': '用户名不能为空'}), 400
            if not data.get('password'):
                return jsonify({'success': False, 'message': '密码不能为空'}), 400

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
                return jsonify({'success': True, 'message': message})
            else:
                return jsonify({'success': False, 'message': message}), 400
        except Exception as e:
            return jsonify({'success': False, 'message': f'添加用户失败：{str(e)}'}), 500

    @app.route('/unified/api/users/<int:user_id>', methods=['PUT'])
    @login_required(roles=['admin'])
    def unified_update_user(user_id):
        """更新统一用户"""
        try:
            data = request.get_json()

            conn = get_unified_kb_conn()
            if not conn:
                return jsonify({'success': False, 'message': '数据库连接失败'}), 500

            cursor = conn.cursor()

            # 构建更新SQL
            update_fields = []
            update_values = []

            if data.get('display_name') is not None:
                update_fields.append('display_name = %s')
                update_values.append(data['display_name'])

            if data.get('real_name') is not None:
                update_fields.append('real_name = %s')
                update_values.append(data['real_name'])

            if data.get('role'):
                update_fields.append('role = %s')
                update_values.append(data['role'])

            if data.get('status'):
                update_fields.append('status = %s')
                update_values.append(data['status'])

            if data.get('email') is not None:
                update_fields.append('email = %s')
                update_values.append(data['email'])

            if data.get('password'):
                # 生成新的 werkzeug 密码哈希
                password_hash = generate_password_hash(data['password'])
                update_fields.append('password_hash = %s')
                update_values.append(password_hash)
                update_fields.append('password_type = %s')
                update_values.append('werkzeug')

            update_values.append(user_id)

            if update_fields:
                sql = f"UPDATE `users` SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(sql, update_values)
                conn.commit()

            cursor.close()
            conn.close()

            return jsonify({'success': True, 'message': '用户更新成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'更新用户失败：{str(e)}'}), 500

    @app.route('/unified/api/users/<int:user_id>', methods=['DELETE'])
    @login_required(roles=['admin'])
    def unified_delete_user(user_id):
        """删除统一用户"""
        try:
            conn = get_unified_kb_conn()
            if not conn:
                return jsonify({'success': False, 'message': '数据库连接失败'}), 500

            cursor = conn.cursor()

            # 检查是否是当前登录用户
            cursor.execute("SELECT username FROM `users` WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user and user[0] == session.get('username'):
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '不能删除当前登录用户'}), 400

            cursor.execute("DELETE FROM `users` WHERE id = %s", (user_id,))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({'success': True, 'message': '用户删除成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'删除用户失败：{str(e)}'}), 500

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
                return jsonify({'success': False, 'message': '数据库连接失败'}), 500

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

            return jsonify({'success': True, 'data': users})
        except Exception as e:
            return jsonify({'success': False, 'message': f'获取用户列表失败：{str(e)}'}), 500

    @app.route('/unified/api/case-users', methods=['POST'])
    @login_required(roles=['admin'])
    def unified_add_case_user():
        """添加工单系统用户"""
        try:
            data = request.get_json()

            if not data.get('username'):
                return jsonify({'success': False, 'message': '用户名不能为空'}), 400
            if not data.get('password'):
                return jsonify({'success': False, 'message': '密码不能为空'}), 400
            if not data.get('email'):
                return jsonify({'success': False, 'message': '邮箱不能为空'}), 400

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
                return jsonify({'success': True, 'message': message})
            else:
                return jsonify({'success': False, 'message': message}), 400
        except Exception as e:
            return jsonify({'success': False, 'message': f'添加用户失败：{str(e)}'}), 500

    @app.route('/unified/api/case-users/<int:user_id>', methods=['PUT'])
    @login_required(roles=['admin'])
    def unified_update_case_user(user_id):
        """更新工单系统用户"""
        try:
            data = request.get_json()

            conn = get_unified_kb_conn()
            if not conn:
                return jsonify({'success': False, 'message': '数据库连接失败'}), 500

            cursor = conn.cursor()

            # 构建更新SQL
            update_fields = []
            update_values = []

            if data.get('real_name') is not None:
                update_fields.append('real_name = %s')
                update_values.append(data['real_name'])

            if data.get('display_name') is not None:
                update_fields.append('display_name = %s')
                update_values.append(data['display_name'])

            if data.get('role'):
                update_fields.append('role = %s')
                update_values.append(data['role'])

            if data.get('email') is not None:
                update_fields.append('email = %s')
                update_values.append(data['email'])

            if data.get('password'):
                # 更新时统一使用 werkzeug 密码
                password_hash = generate_password_hash(data['password'])
                update_fields.append('password_hash = %s')
                update_values.append(password_hash)
                update_fields.append('password_type = %s')
                update_values.append('werkzeug')

            update_values.append(user_id)

            if update_fields:
                sql = f"UPDATE `users` SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(sql, update_values)
                conn.commit()

            cursor.close()
            conn.close()

            return jsonify({'success': True, 'message': '用户更新成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'更新用户失败：{str(e)}'}), 500

    @app.route('/unified/api/case-users/<int:user_id>', methods=['DELETE'])
    @login_required(roles=['admin'])
    def unified_delete_case_user(user_id):
        """删除工单系统用户"""
        try:
            conn = get_unified_kb_conn()
            if not conn:
                return jsonify({'success': False, 'message': '数据库连接失败'}), 500

            cursor = conn.cursor()

            # 检查是否是当前登录用户
            cursor.execute("SELECT username FROM `users` WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user and user[0] == session.get('username'):
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '不能删除当前登录用户'}), 400

            cursor.execute("DELETE FROM `users` WHERE id = %s", (user_id,))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({'success': True, 'message': '用户删除成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'删除用户失败：{str(e)}'}), 500

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

            return jsonify({'success': True, 'data': stats})
        except Exception as e:
            return jsonify({'success': False, 'message': f'获取统计信息失败：{str(e)}'}), 500

    # 管理员重置用户密码路由
    @app.route('/auth/api/reset-password/<int:user_id>', methods=['POST'])
    @login_required(roles=['admin'])
    def reset_user_password(user_id):
        """管理员重置指定用户的密码"""
        try:
            conn = get_unified_kb_conn()
            if not conn:
                return jsonify({'success': False, 'message': '数据库连接失败'}), 500

            cursor = conn.cursor()

            # 获取用户信息
            cursor.execute("SELECT username FROM `users` WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '用户不存在'}), 404

            username = user[0]

            # 检查是否是admin用户
            if username == 'admin':
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '不能重置admin用户密码'}), 400

            data = request.get_json()
            new_password = data.get('password', '').strip()

            if not new_password:
                return jsonify({'success': False, 'message': '请输入新密码'}), 400

            if len(new_password) < 6:
                return jsonify({'success': False, 'message': '密码长度至少为6位'}), 400

            # 生成新的 werkzeug 密码哈希
            password_hash = generate_password_hash(new_password)

            update_sql = "UPDATE `users` SET password_hash = %s, password_type = %s, updated_at = NOW() WHERE id = %s"
            cursor.execute(update_sql, (password_hash, 'werkzeug', user_id))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({'success': True, 'message': f'用户 {username} 的密码已重置'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'重置密码失败：{str(e)}'}), 500


# ==================== SocketIO事件注册 ====================
def register_socketio_events(socketio):
    """注册SocketIO事件"""

    @socketio.on('connect')
    def handle_connect():
        print(f'客户端已连接：{request.sid}')

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'客户端已断开连接：{request.sid}')

    @socketio.on('join_ticket')
    def handle_join_ticket(data):
        ticket_id = data.get('ticket_id')
        user_type = data.get('user_type')
        user_name = data.get('user_name', '匿名用户')

        if ticket_id:
            room = f'ticket_{ticket_id}'
            join_room(room)
            print(f'{user_name} ({user_type}) 加入了工单 {ticket_id} 聊天室')

            emit('notification', {
                'message': f'{user_name} 加入了聊天',
                'user_type': user_type
            }, room=room, skip_sid=request.sid)

    @socketio.on('leave_ticket')
    def handle_leave_ticket(data):
        ticket_id = data.get('ticket_id')
        user_type = data.get('user_type')
        user_name = data.get('user_name', '匿名用户')

        if ticket_id:
            room = f'ticket_{ticket_id}'
            leave_room(room)
            print(f'{user_name} ({user_type}) 离开了工单 {ticket_id} 聊天室')

            emit('notification', {
                'message': f'{user_name} 离开了聊天',
                'user_type': user_type
            }, room=room, skip_sid=request.sid)

    @socketio.on('send_message')
    def handle_send_message(data):
        ticket_id = data.get('ticket_id')
        sender = data.get('sender')
        sender_name = data.get('sender_name')
        content = data.get('content')

        if not all([ticket_id, sender, sender_name, content]):
            return {'success': False, 'message': '消息参数不完整'}

        try:
            conn = get_case_db_connection()
            if not conn:
                return {'success': False, 'message': '数据库连接失败'}
            cursor = conn.cursor()

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            insert_sql = """
                INSERT INTO messages (ticket_id, sender, sender_name, content, send_time)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (ticket_id, sender, sender_name, content, now))
            conn.commit()

            message_id = cursor.lastrowid
            cursor.close()
            conn.close()

            message_data = {
                'id': message_id,
                'ticket_id': ticket_id,
                'sender': sender,
                'sender_name': sender_name,
                'content': content,
                'send_time': now
            }

            room = f'ticket_{ticket_id}'
            emit('new_message', message_data, room=room)

            return {'success': True, 'message': '消息发送成功'}
        except Exception as e:
            print(f"发送消息异常：{e}")
            return {'success': False, 'message': f'发送失败：{str(e)}'}


# ==================== 数据库初始化 ====================
def init_case_database():
    """初始化工单系统数据库表"""
    conn = get_case_db_connection()
    if not conn:
        return

    cursor = conn.cursor()

    create_ticket_sql = """
        CREATE TABLE IF NOT EXISTS tickets (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增ID',
            ticket_id VARCHAR(32) NOT NULL UNIQUE COMMENT '工单唯一标识ID',
            customer_name VARCHAR(100) NOT NULL COMMENT '客户名称',
            customer_contact VARCHAR(50) NOT NULL COMMENT '客户联系方式',
            customer_email VARCHAR(100) NOT NULL COMMENT '客户邮箱',
            product VARCHAR(50) NOT NULL COMMENT '涉及产品',
            issue_type VARCHAR(20) NOT NULL COMMENT '问题类型',
            priority VARCHAR(10) NOT NULL COMMENT '工单优先级',
            title VARCHAR(200) NOT NULL COMMENT '问题标题',
            content TEXT NOT NULL COMMENT '问题详情',
            status VARCHAR(10) DEFAULT 'pending' COMMENT '工单状态',
            create_time DATETIME NOT NULL COMMENT '创建时间',
            update_time DATETIME NOT NULL COMMENT '更新时间',
            INDEX idx_ticket_id (ticket_id),
            INDEX idx_customer_name (customer_name),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单系统主表'
    """

    create_message_sql = """
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '消息ID',
            ticket_id VARCHAR(32) NOT NULL COMMENT '工单ID',
            sender VARCHAR(20) NOT NULL COMMENT '发送者',
            sender_name VARCHAR(100) NOT NULL COMMENT '发送者名称',
            content TEXT NOT NULL COMMENT '消息内容',
            send_time DATETIME NOT NULL COMMENT '发送时间',
            INDEX idx_ticket_id (ticket_id),
            INDEX idx_send_time (send_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单聊天消息表'
    """

    try:
        cursor.execute(create_ticket_sql)
        cursor.execute(create_message_sql)
        conn.commit()
        print("工单系统数据库表初始化成功")
    except pymysql.MySQLError as e:
        conn.rollback()
        print(f"工单系统数据库初始化失败：{e}")
    finally:
        cursor.close()
        conn.close()
