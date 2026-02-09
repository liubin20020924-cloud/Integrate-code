"""
统一路由模块 - 整合所有系统的路由
包含：官网、知识库、工单、统一用户管理

重构说明：
- 使用统一的响应处理模块 (common.response)
- 使用结构化日志 (common.logger)
- 使用用户服务层 (services.user_service)
- 使用输入验证 (common.validators)
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, Response, send_from_directory, jsonify
from trilium_py.client import ETAPI
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
import uuid
import pymysql
import os
from werkzeug.security import generate_password_hash, check_password_hash

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入配置和公共模块
import config
from common.db_manager import get_connection
from common.response import (
    success_response, error_response, not_found_response,
    unauthorized_response, forbidden_response, validation_error_response,
    server_error_response
)
from common.logger import logger, log_exception, log_request
from common.validators import (
    validate_email, validate_password, validate_username,
    validate_phone, validate_required, validate_user_data
)
from services.user_service import UserService

from common.kb_utils import (
    fetch_all_records, fetch_record_by_id, fetch_records_by_name_with_pagination,
    get_total_count, fetch_records_with_pagination, get_kb_db_connection
)
from common.unified_auth import (
    authenticate_user, get_current_user as get_kb_current_user,
    login_required, create_user, update_user_password
)


# ==================== 全局变量 ====================
DEBUG_MODE = False


# ==================== 辅助函数 ====================
def get_case_db_connection():
    """获取工单系统数据库连接"""
    conn = get_connection('case')
    if not conn:
        logger.error("无法连接到工单数据库")
    return conn


def get_kb_conn():
    """获取知识库数据库连接"""
    return get_kb_db_connection()


def get_unified_kb_conn():
    """获取知识库数据库连接（用于统一用户管理）"""
    conn = get_connection('kb')
    if not conn:
        logger.error("无法连接到知识库数据库")
    return conn


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
        logger.error(f"服务器内部错误: {error}")
        return "500 - Internal Server Error", 500

    # 会话管理中间件
    @app.before_request
    def before_request():
        session.permanent = False

    # ==================== 官网系统路由 ====================

    @app.route('/')
    def home_index():
        """首页"""
        return render_template('home/index.html', now=datetime.now)

    @app.route('/test-images')
    def test_images():
        """图片测试页面"""
        return render_template('home_test_images.html')

    @app.route('/view-messages')
    def view_messages():
        """留言管理页面"""
        return render_template('home/admin_messages.html')

    @app.route('/api/contact', methods=['POST'])
    def contact():
        """联系表单提交"""
        try:
            data = request.get_json()
            
            # 验证必填字段
            is_valid, errors = validate_required(data, ['name', 'email', 'message'])
            if not is_valid:
                return validation_error_response(errors)
            
            # 验证邮箱
            is_valid, msg = validate_email(data['email'])
            if not is_valid:
                return error_response(msg, 400)
            
            logger.info(f"收到联系表单: {data['name']} <{data['email']}>")
            return success_response(message='留言提交成功')
        except Exception as e:
            log_exception(logger, "提交联系表单失败")
            return server_error_response(f'提交失败：{str(e)}')

    @app.route('/api/messages', methods=['GET'])
    def get_messages():
        """获取留言列表"""
        return success_response(data={'messages': []}, message='查询成功')

    @app.route('/messages')
    def messages():
        """留言管理"""
        return render_template('home/admin_messages.html')

    @app.route('/dashboard')
    def dashboard():
        """管理仪表板"""
        return render_template('home/admin_dashboard.html')

    # ==================== 知识库系统路由 - 认证 ====================

    @app.route('/kb/auth/login', methods=['GET', 'POST'])
    def kb_login():
        """登录页面"""
        if get_kb_current_user():
            logger.info("用户已登录，重定向到知识库首页")
            return redirect(url_for('kb_index'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            if not username or not password:
                return render_template('kb/login.html', error="请输入用户名和密码")

            success, result = authenticate_user(username, password)

            if success:
                user_info = result
                session['user_id'] = user_info['id']
                session['username'] = user_info['username']
                session['display_name'] = user_info['display_name']
                session['role'] = user_info['role']
                session['login_time'] = datetime.now().isoformat()
                session.permanent = False

                logger.info(f"用户 {username} 登录成功")

                next_url = request.form.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(url_for('kb_index'))
            else:
                logger.warning(f"用户 {username} 登录失败: {result}")
                return render_template('kb/login.html', error=result, username=username)

        return render_template('kb/login.html')

    @app.route('/kb/auth/logout')
    def kb_logout():
        """退出登录"""
        username = session.get('username', 'unknown')
        session.clear()
        logger.info(f"用户 {username} 退出登录")
        return redirect(url_for('kb_login'))

    @app.route('/kb/auth/check-login')
    def kb_check_login():
        """检查登录状态"""
        user = get_kb_current_user()
        if user:
            return success_response(data={'user': user}, message='已登录')
        return unauthorized_response(message='未登录')

    # 兼容旧的路由路径
    @app.route('/auth/check-login')
    def auth_check_login():
        """检查登录状态 - 兼容路由"""
        return kb_check_login()

    @app.route('/auth/login')
    def auth_login():
        """登录页面 - 兼容路由"""
        return redirect(url_for('kb_login'))

    @app.route('/auth/logout')
    def auth_logout():
        """退出登录 - 兼容路由"""
        return kb_logout()

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
        return render_template('kb/change_password.html')

    # 修改密码API路由
    @app.route('/auth/api/change-password', methods=['POST'])
    def change_password():
        """修改当前用户密码"""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return unauthorized_response(message='未登录')

            data = request.get_json()
            old_password = data.get('old_password', '').strip()
            new_password = data.get('new_password', '').strip()

            if not old_password or not new_password:
                return error_response('请输入旧密码和新密码', 400)

            # 验证新密码
            is_valid, msg = validate_password(new_password)
            if not is_valid:
                return error_response(msg, 400)

            # 验证旧密码
            username = session.get('username')
            success, result = authenticate_user(username, old_password)

            if not success:
                logger.warning(f"用户 {username} 修改密码失败：旧密码错误")
                return error_response('旧密码错误', 400)

            # 更新密码
            success, message = update_user_password(user_id, new_password)

            if success:
                logger.info(f"用户 {username} 修改密码成功")
                return success_response(message='密码修改成功')
            else:
                return error_response(message, 500)

        except Exception as e:
            log_exception(logger, "修改密码失败")
            return server_error_response(f'修改密码失败：{str(e)}')

    # Trilium 搜索路由
    @app.route('/api/trilium/search')
    def trilium_search():
        """Trilium 搜索 - 使用 trilium-py 模块"""
        try:
            query = request.args.get('q', '').strip()
            limit = int(request.args.get('limit', 30))

            if not query:
                return error_response('请输入搜索关键词', 400)

            # 检查 Trilium 配置
            if not hasattr(config, 'TRILIUM_SERVER_URL') or not config.TRILIUM_SERVER_URL:
                logger.error("Trilium 服务未配置")
                return error_response('Trilium 服务未配置', 500)

            logger.info(f"开始Trilium搜索: {query}")

            # 使用 trilium-py 模块进行搜索
            try:
                from trilium_py.client import ETAPI

                server_url = config.TRILIUM_SERVER_URL.rstrip('/')
                token = config.TRILIUM_TOKEN

                # 如果没有token，尝试使用密码登录
                if not token and hasattr(config, 'TRILIUM_LOGIN_PASSWORD'):
                    ea = ETAPI(server_url)
                    token = ea.login(config.TRILIUM_LOGIN_PASSWORD)
                    logger.info("使用密码登录Trilium成功")
                    if not token:
                        return error_response('Trilium登录失败，请检查密码配置', 500)

                # 创建ETAPI客户端
                ea = ETAPI(server_url, token)

                # 执行搜索
                # 注意：根据 trilium-py 文档，limit 只有在使用 orderBy 时才有效
                # 对于简单搜索，我们不使用 limit，而是获取所有结果后再截取
                search_results = ea.search_note(search=query)

                # 格式化返回结果
                results = []
                if 'results' in search_results:
                    # 限制返回结果数量
                    for i, result in enumerate(search_results['results']):
                        if i >= limit:
                            break
                        results.append({
                            'noteId': result.get('noteId', ''),
                            'title': result.get('title', ''),
                            'type': result.get('type', 'text'),
                            'dateModified': result.get('utcDateModified', '')
                        })

                logger.info(f"Trilium搜索完成: 找到 {len(results)} 条结果")
                return success_response(
                    data={'results': results, 'query': query, 'count': len(results)},
                    message='搜索完成'
                )

            except ImportError as e:
                logger.error(f"trilium-py 模块未安装: {e}")
                return error_response('trilium-py 模块未安装，请运行: pip install trilium-py', 500)
            except Exception as e:
                logger.error(f"Trilium搜索异常: {str(e)}")
                return error_response(f'Trilium搜索失败: {str(e)}', 500)

        except Exception as e:
            log_exception(logger, "Trilium搜索失败")
            return server_error_response(f'搜索失败：{str(e)}')

    # Trilium 内容加载路由
    @app.route('/api/trilium/content')
    def trilium_content():
        """获取 Trilium 笔记内容"""
        try:
            kb_number = request.args.get('kb_number', '').strip()
            trilium_url = request.args.get('trilium_url', '').strip()

            if not trilium_url:
                return error_response(message='缺少 Trilium URL 参数')

            # 从数据库获取知识库信息
            title = '知识库内容'
            modified = None

            if kb_number:
                try:
                    conn = get_kb_conn()
                    if conn:
                        cursor = conn.cursor(pymysql.cursors.DictCursor)
                        cursor.execute(
                            "SELECT KB_Name, KB_UpdateTime FROM `KB-info` WHERE KB_Number = %s",
                            (kb_number,)
                        )
                        kb_info = cursor.fetchone()
                        cursor.close()
                        conn.close()

                        if kb_info:
                            title = kb_info['KB_Name']
                            if kb_info['KB_UpdateTime']:
                                modified = kb_info['KB_UpdateTime'].strftime('%Y-%m-%d %H:%M:%S')
                except Exception as db_error:
                    logger.warning(f"获取知识库信息失败: {db_error}")

            # 构建完整的 Trilium URL
            if not trilium_url.startswith('http'):
                if hasattr(config, 'TRILIUM_SERVER_URL') and config.TRILIUM_SERVER_URL:
                    base_url = config.TRILIUM_SERVER_URL.rstrip('/')
                    trilium_url = f"{base_url}/{trilium_url}"
                else:
                    return error_response(message='Trilium 服务未配置')

            # 检查 Trilium Token 配置
            if not hasattr(config, 'TRILIUM_TOKEN') or not config.TRILIUM_TOKEN:
                return error_response(message='Trilium 认证未配置')

            # 使用 Trilium 辅助类获取内容
            from common.trilium_helper import get_trilium_helper

            logger.info(f"开始获取Trilium内容: trilium_url={trilium_url}, kb_number={kb_number}")

            trilium_helper = get_trilium_helper()
            success, content, message = trilium_helper.get_note_content(trilium_url)

            logger.info(f"Trilium内容获取结果: success={success}, message={message}, content_length={len(content) if content else 0}")

            if success:
                return success_response(data={
                    'content': content,
                    'title': title,
                    'modified': modified,
                    'kb_number': kb_number,
                    'url': trilium_url
                }, message='获取成功')
            else:
                # 返回错误信息，但不是 501 错误
                logger.error(f"Trilium内容获取失败: {message}")
                return error_response(message=message)

        except Exception as e:
            log_exception(logger, "加载Trilium内容失败")
            return server_error_response(message=f'加载内容失败：{str(e)}')

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

            return render_template('kb/index.html', records=records,
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
            logger.error(error_msg)
            return render_template('kb/index.html', records=[],
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
            return render_template('kb/index.html', records=[],
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
                logger.info(f"搜索知识库记录: {record_id}")
                return render_template('kb/index.html', records=[record],
                                     total_count=1,
                                     showing_count=1,
                                     page=page,
                                     per_page=15,
                                     total_pages=1,
                                     search_id=search_id,
                                     is_search=True)
            else:
                return render_template('kb/index.html', records=[],
                                     error=f"未找到ID为 {search_id} 的记录",
                                     total_count=get_total_count(),
                                     showing_count=0,
                                     page=1,
                                     per_page=15,
                                     total_pages=1,
                                     search_id=search_id,
                                     is_search=True)
        except ValueError:
            return render_template('kb/index.html', records=[],
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
            return success_response(data={'records': records, 'count': len(records)}, message='查询成功')
        except Exception as e:
            log_exception(logger, "获取所有知识库记录失败")
            return server_error_response(f"数据库错误: {str(e)}")

    @app.route('/kb/search/name', methods=['POST'])
    def kb_search_by_name():
        """按名称搜索"""
        name = request.form.get('name', '').strip()
        page = request.form.get('page', 1, type=int)
        per_page = request.form.get('per_page', 15, type=int)

        if not name:
            return error_response('请输入知识库名称', 400)

        try:
            records, total_count = fetch_records_by_name_with_pagination(name, page, per_page)
            total_pages = (total_count + per_page - 1) // per_page
            return success_response(
                data={
                    'records': records,
                    'count': len(records),
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages
                },
                message='搜索完成'
            )
        except Exception as e:
            log_exception(logger, "按名称搜索知识库记录失败")
            return server_error_response(f"搜索错误: {str(e)}")

    @app.route('/kb/api/stats')
    def kb_get_stats():
        """统计信息"""
        try:
            count = get_total_count()
            return success_response(data={'total_count': count}, message='查询成功')
        except Exception as e:
            log_exception(logger, "获取知识库统计信息失败")
            return server_error_response(f"统计信息获取失败: {str(e)}")

    # ==================== 知识库系统路由 - 管理 ====================

    @app.route('/kb/MGMT/')
    @login_required(roles=['admin'])
    def kb_management():
        """管理页面 - 使用分页加载优化性能"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 20
            records, total_count = fetch_records_with_pagination(page, per_page)
            user = get_kb_current_user()

            total_pages = (total_count + per_page - 1) // per_page
            showing_start = (page - 1) * per_page + 1
            showing_end = min(page * per_page, total_count)

            return render_template('kb/management.html', records=records,
                                 total_count=total_count,
                                 showing_count=showing_end - showing_start + 1 if records else 0,
                                 page=page,
                                 per_page=per_page,
                                 total_pages=total_pages,
                                 showing_start=showing_start,
                                 showing_end=showing_end,
                                 current_user=user,
                                 debug_mode=DEBUG_MODE,
                                 max=max,
                                 min=min)
        except Exception as e:
            logger.error(f"加载知识库管理页面失败: {e}")
            return render_template('kb/management.html', records=[],
                                 error=str(e),
                                 total_count=0,
                                 page=1,
                                 per_page=20,
                                 total_pages=1,
                                 max=max,
                                 min=min)

    @app.route('/kb/auth/users')
    @login_required(roles=['admin'])
    def kb_user_management():
        """用户管理页面"""
        try:
            conn = get_unified_kb_conn()
            if not conn:
                return render_template('kb/user_management.html', users=[],
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

            return render_template('kb/user_management.html', users=users,
                                 login_logs=login_logs,
                                 total_count=len(users) if users else 0)
        except Exception as e:
            log_exception(logger, "加载知识库用户管理页面失败")
            return render_template('kb/user_management.html', users=[],
                                 login_logs=[],
                                 error=str(e),
                                 total_count=0)

    # 兼容旧的用户管理路由
    @app.route('/auth/users')
    @login_required(roles=['admin'])
    def auth_user_management():
        """用户管理页面 - 兼容路由"""
        return redirect(url_for('kb_user_management'))

    # 知识库用户管理API（使用新的UserService）
    @app.route('/auth/api/add-user', methods=['POST'])
    @login_required(roles=['admin'])
    def kb_add_user():
        """添加知识库用户"""
        try:
            data = request.get_json()
            
            # 验证输入
            is_valid, errors = validate_user_data(data)
            if not is_valid:
                return validation_error_response(errors)

            # 添加必填字段验证
            if not data.get('username') or not data.get('password'):
                return error_response('用户名和密码不能为空', 400)

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
                logger.info(f"添加用户 {data['username']} 成功")
                return success_response(message=message)
            else:
                return error_response(message, 400)
        except Exception as e:
            log_exception(logger, "添加用户失败")
            return server_error_response(f'添加用户失败：{str(e)}')

    @app.route('/auth/api/update-user/<int:user_id>', methods=['PUT'])
    @login_required(roles=['admin'])
    def kb_update_user(user_id):
        """更新知识库用户（使用新的UserService）"""
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
                logger.info(f"更新用户 {user_id} 成功")
                return success_response(message=message)
            else:
                return error_response(message, 400)

        except Exception as e:
            log_exception(logger, "更新用户失败")
            return server_error_response(f'更新用户失败：{str(e)}')

    @app.route('/auth/api/delete-user/<int:user_id>', methods=['DELETE'])
    @login_required(roles=['admin'])
    def kb_delete_user(user_id):
        """删除知识库用户（使用新的UserService）"""
        try:
            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response('数据库连接失败')

            # 检查是否是admin用户
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM `users` WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user and user[0] == 'admin':
                cursor.close()
                conn.close()
                return error_response('不能删除admin用户', 400)
            cursor.close()

            # 调用服务层
            success, message = UserService.delete_user(conn, user_id)
            conn.close()

            if success:
                logger.info(f"删除用户 {user_id} 成功")
                return success_response(message=message)
            else:
                return error_response(message, 400)

        except Exception as e:
            log_exception(logger, "删除用户失败")
            return server_error_response(f'删除用户失败：{str(e)}')

    @app.route('/kb/MGMT/api/add', methods=['POST'])
    @login_required(roles=['admin'])
    def kb_add_record():
        """添加记录"""
        try:
            data = request.get_json()

            # 验证必填字段
            is_valid, errors = validate_required(data, ['KB_Number', 'KB_Name'])
            if not is_valid:
                return validation_error_response(errors)

            existing = fetch_record_by_id(data['KB_Number'])
            if existing:
                return error_response(f"编号 {data['KB_Number']} 已存在", 400)

            connection = get_kb_conn()
            if connection is None:
                return server_error_response('数据库连接失败')

            with connection.cursor() as cursor:
                sql = "INSERT INTO `KB-info` (KB_Number, KB_Name, KB_link) VALUES (%s, %s, %s)"
                cursor.execute(sql, (data['KB_Number'], data['KB_Name'], data.get('KB_link', '')))
                connection.commit()
                affected_rows = cursor.rowcount

            connection.close()

            if affected_rows > 0:
                logger.info(f"添加知识库记录 {data['KB_Number']} 成功")
                return success_response(message='记录添加成功', data={'id': data['KB_Number']})
            else:
                return error_response('添加记录失败', 500)
        except Exception as e:
            log_exception(logger, "添加知识库记录失败")
            return server_error_response(f"添加记录时发生错误: {str(e)}")

    @app.route('/kb/MGMT/api/update/<int:record_id>', methods=['PUT'])
    @login_required(roles=['admin'])
    def kb_update_record(record_id):
        """更新记录"""
        try:
            data = request.get_json()
            existing = fetch_record_by_id(record_id)
            if not existing:
                return error_response(f"记录 {record_id} 不存在", 404)

            connection = get_kb_conn()
            if connection is None:
                return server_error_response('数据库连接失败')

            with connection.cursor() as cursor:
                sql = "UPDATE `KB-info` SET KB_Name = %s, KB_link = %s WHERE KB_Number = %s"
                cursor.execute(sql, (data.get('KB_Name', existing['KB_Name']), data.get('KB_link', existing['KB_link']), record_id))
                connection.commit()
                affected_rows = cursor.rowcount

            connection.close()

            if affected_rows > 0:
                logger.info(f"更新知识库记录 {record_id} 成功")
                return success_response(message='记录更新成功')
            else:
                return error_response('更新记录失败', 500)
        except Exception as e:
            log_exception(logger, "更新知识库记录失败")
            return server_error_response(f"更新记录时发生错误: {str(e)}")

    @app.route('/kb/MGMT/api/delete/<int:record_id>', methods=['DELETE'])
    @login_required(roles=['admin'])
    def kb_delete_record(record_id):
        """删除记录"""
        try:
            existing = fetch_record_by_id(record_id)
            if not existing:
                return error_response(f"记录 {record_id} 不存在", 404)

            connection = get_kb_conn()
            if connection is None:
                return server_error_response('数据库连接失败')

            with connection.cursor() as cursor:
                sql = "DELETE FROM `KB-info` WHERE KB_Number = %s"
                cursor.execute(sql, (record_id,))
                connection.commit()
                affected_rows = cursor.rowcount

            connection.close()

            if affected_rows > 0:
                logger.info(f"删除知识库记录 {record_id} 成功")
                return success_response(message='记录删除成功')
            else:
                return error_response('删除记录失败', 500)
        except Exception as e:
            log_exception(logger, "删除知识库记录失败")
            return server_error_response(f"删除记录时发生错误: {str(e)}")

    # 批量添加记录API
    @app.route('/kb/MGMT/api/batch-add', methods=['POST'])
    @login_required(roles=['admin'])
    def kb_batch_add_record():
        """批量添加记录"""
        try:
            data = request.get_json()
            records = data.get('records', [])

            if not records:
                return error_response('没有要添加的记录', 400)

            connection = get_kb_conn()
            if connection is None:
                return server_error_response('数据库连接失败')

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

            logger.info(f"批量添加知识库记录完成: 成功{success_count}, 重复{duplicate_count}, 失败{failed_count}")
            return success_response(
                message=f'批量添加完成：成功 {success_count} 条，跳过重复 {duplicate_count} 条，失败 {failed_count} 条',
                data={
                    'summary': {
                        'total': len(records),
                        'success': success_count,
                        'duplicate': duplicate_count,
                        'failed': failed_count
                    },
                    'failed_records': failed_records
                }
            )
        except Exception as e:
            log_exception(logger, "批量添加知识库记录失败")
            return server_error_response(f"批量添加记录时发生错误: {str(e)}")

    # 批量删除记录API
    @app.route('/kb/MGMT/api/batch-delete', methods=['POST'])
    @login_required(roles=['admin'])
    def kb_batch_delete_records():
        """批量删除记录"""
        try:
            data = request.get_json()
            ids = data.get('ids', [])

            if not ids:
                return error_response('没有要删除的记录', 400)

            connection = get_kb_conn()
            if connection is None:
                return server_error_response('数据库连接失败')

            with connection.cursor() as cursor:
                placeholders = ','.join(['%s'] * len(ids))
                sql = f"DELETE FROM `KB-info` WHERE KB_Number IN ({placeholders})"
                cursor.execute(sql, ids)
                affected_rows = cursor.rowcount
                connection.commit()

            connection.close()

            logger.info(f"批量删除知识库记录完成: {affected_rows} 条")
            return success_response(
                message=f'成功删除 {affected_rows} 条记录'
            )
        except Exception as e:
            log_exception(logger, "批量删除知识库记录失败")
            return server_error_response(f"批量删除记录时发生错误: {str(e)}")

    # 导出数据API
    @app.route('/kb/MGMT/api/export', methods=['GET'])
    @login_required(roles=['admin'])
    def kb_export_data():
        """导出所有数据"""
        try:
            records = fetch_all_records()
            logger.info(f"导出知识库数据: {len(records)} 条记录")
            return success_response(
                message='数据导出成功',
                data={
                    'data': records,
                    'count': len(records)
                }
            )
        except Exception as e:
            log_exception(logger, "导出知识库数据失败")
            return server_error_response(f"导出数据时发生错误: {str(e)}")

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

            response_data = {
                'records': records,
                'total_count': total_count,
                'showing_count': showing_end - showing_start + 1 if records else 0,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'showing_start': showing_start,
                'showing_end': showing_end
            }
            return jsonify({
                'success': True,
                'message': '查询成功',
                **response_data
            })
        except Exception as e:
            log_exception(logger, "获取知识库分页记录失败")
            return server_error_response(
                message=f"获取记录失败: {str(e)}"
            )

    # 系统状态API
    @app.route('/kb/api/attachments/<path:attachment_path>', methods=['GET'])
    @login_required(roles=['admin', 'user'])
    def proxy_kb_image(attachment_path):
        """代理 Trilium 知识库的图片请求，使用 ETAPI"""
        try:
            # attachment_path 格式: ZjD0OZLY4aWU/image/f6f83bfe35c1711a70ed62a985ab1a92.png
            # 提取 attachment_id (第一部分)
            parts = attachment_path.split('/')
            if not parts or len(parts) < 1:
                return Response('Invalid attachment path', status=400)

            attachment_id = parts[0]
            logger.info(f"代理图片请求: attachment_id={attachment_id}, full_path={attachment_path}")

            # 使用 trilium-py 的 ETAPI 获取附件内容
            ea = ETAPI(config.TRILIUM_SERVER_URL, config.TRILIUM_TOKEN)

            # 获取附件内容
            attachment_content = ea.get_attachment_content(attachment_id)

            if attachment_content:
                # 返回图片内容
                return Response(
                    attachment_content,
                    mimetype='image/png',
                    headers={
                        'Cache-Control': 'public, max-age=86400',  # 缓存 1 天
                    }
                )
            else:
                logger.error(f"从 Trilium 获取图片失败: attachment_id={attachment_id}")
                return Response('Image not found', status=404)
        except Exception as e:
            log_exception(logger, "代理 Trilium 图片失败")
            return Response(f'Failed to proxy image: {str(e)}', status=500)

    @app.route('/kb/MGMT/api/system-status', methods=['GET'])
    @login_required(roles=['admin'])
    def kb_system_status():
        """获取系统状态"""
        try:
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
                    logger.error(f"获取知识库系统状态失败: {e}")
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

            return success_response(
                data={
                    'system_health': system_health,
                    'database_connected': database_connected,
                    'total_records': total_records,
                    'user_count': user_count,
                    'latest_record_time': latest_record_time,
                    'current_user': get_kb_current_user(),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                message='查询成功'
            )
        except Exception as e:
            log_exception(logger, "获取知识库系统状态失败")
            return server_error_response(message=f"获取系统状态失败: {str(e)}")

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

            logger.info(f"调试模式已{'开启' if debug_mode else '关闭'}")
            return success_response(
                message=f'调试模式已{"开启" if debug_mode else "关闭"}',
                data={'debug_mode': debug_mode}
            )
        except Exception as e:
            log_exception(logger, "切换调试模式失败")
            return server_error_response(message=f"切换调试模式失败: {str(e)}")

    # 获取调试信息API
    @app.route('/kb/MGMT/debug', methods=['GET'])
    @login_required(roles=['admin'])
    def kb_debug_info():
        """获取调试信息"""
        try:
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

            return success_response(data={'data': debug_data}, message='查询成功')
        except Exception as e:
            log_exception(logger, "获取调试信息失败")
            return server_error_response(message=f"获取调试信息失败: {str(e)}")

    # 系统清理API
    @app.route('/kb/MGMT/api/cleanup', methods=['POST'])
    @login_required(roles=['admin'])
    def kb_system_cleanup():
        """系统清理"""
        try:
            # 这里可以添加清理逻辑，比如清理临时文件、旧日志等
            logger.info("执行系统清理")
            return success_response(message='系统清理完成')
        except Exception as e:
            log_exception(logger, "系统清理失败")
            return server_error_response(message=f"系统清理失败: {str(e)}")

    # ==================== 工单系统路由 ====================

    @app.route('/case/')
    def case_index():
        """首页"""
        return render_template('case/login.html')

    @app.route('/case/<path:filename>')
    def case_serve_frontend(filename):
        """提供前端文件"""
        try:
            return render_template(f'case/{filename}')
        except:
            return "404 - 文件未找到", 404

    @app.route('/case/api/login', methods=['POST'])
    def case_login():
        """登录"""
        try:
            log_request(logger, request)
            data = request.get_json()
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

    @app.route('/case/api/register', methods=['POST'])
    def case_register():
        """注册新用户"""
        try:
            log_request(logger, request, '/case/api/register')
            data = request.get_json()
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '').strip()

            # 简单验证
            if not username:
                return error_response(message='用户名不能为空')
            if not email:
                return error_response(message='邮箱不能为空')
            if not password:
                return error_response(message='密码不能为空')

            is_valid_email, email_error = validate_email(email)
            if not is_valid_email:
                return error_response(message=email_error)

            # 使用统一认证创建用户
            success, result = create_user(
                username=username,
                email=email,
                password=password,
                display_name=username,
                real_name=username,
                role='customer'  # 默认注册为客户角色
            )

            if not success:
                return error_response(message=result)

            return success_response(message='注册成功')
        except Exception as e:
            log_exception(logger, "注册失败")
            return server_error_response(message=f'注册失败：{str(e)}')

    @app.route('/case/api/logout', methods=['POST'])
    def case_logout():
        """登出"""
        session.clear()
        return success_response(message='登出成功')

    @app.route('/case/api/user/info', methods=['GET'])
    def case_get_user_info():
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

    @app.route('/case/api/ticket', methods=['POST'])
    def case_create_ticket():
        """创建工单"""
        try:
            log_request(logger, request, '/case/api/ticket')
            data = request.get_json()
            required_fields = [
                'customer_name', 'customer_contact', 'customer_email',
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

            conn = get_case_db_connection()
            if not conn:
                return server_error_response(message='数据库连接失败')
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

            logger.info(f"工单创建成功: {ticket_id}")
            return success_response(data={'ticket_id': ticket_id}, message='工单创建成功')
        except Exception as e:
            log_exception(logger, "工单创建失败")
            return server_error_response(message=f'工单创建失败：{str(e)}')

    @app.route('/case/api/tickets', methods=['GET'])
    def case_get_tickets():
        """获取工单列表"""
        try:
            log_request(logger, request, '/case/api/tickets')
            user_role = session.get('role')
            user_username = session.get('username')

            if not user_role:
                return unauthorized_response(message='未登录')

            status = request.args.get('status', '').strip()
            my_only = request.args.get('my_only', 'false').lower() == 'true'
            conn = get_case_db_connection()
            if not conn:
                return server_error_response(message='数据库连接失败')
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # customer 角色: 只能看到自己创建的工单
            if user_role == 'customer':
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
            # admin/user 角色: 可以查看所有工单，支持 my_only 筛选
            elif user_role in ['admin', 'user']:
                if status and my_only:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE status = %s ORDER BY create_time DESC LIMIT 100
                    """
                    cursor.execute(select_sql, (status,))
                elif status:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE status = %s ORDER BY create_time DESC LIMIT 100
                    """
                    cursor.execute(select_sql, (status,))
                else:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets ORDER BY create_time DESC LIMIT 100
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
            log_exception(logger, "查询工单列表失败")
            return server_error_response(message=f'查询失败：{str(e)}')

    @app.route('/case/api/ticket/<ticket_id>', methods=['GET'])
    def case_get_ticket_detail(ticket_id):
        """获取工单详情"""
        try:
            log_request(logger, request, f'/case/api/ticket/{ticket_id}')
            user_role = session.get('role')
            user_username = session.get('username')

            if not user_role:
                return unauthorized_response(message='未登录')

            conn = get_case_db_connection()
            if not conn:
                return server_error_response(message='数据库连接失败')
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
            log_exception(logger, "查询工单详情失败")
            return server_error_response(message=f'查询失败：{str(e)}')

    @app.route('/case/api/ticket/<ticket_id>/status', methods=['PUT'])
    def case_update_ticket_status(ticket_id):
        """更新工单状态"""
        try:
            log_request(logger, request, f'/case/api/ticket/{ticket_id}/status')
            user_role = session.get('role')
            if not user_role or user_role != 'admin':
                return forbidden_response(message='无权执行此操作')

            data = request.get_json()
            new_status = data.get('status', '').strip()

            valid_statuses = ['pending', 'processing', 'completed', 'closed']
            if new_status not in valid_statuses:
                return error_response(message='工单状态值不合法')

            conn = get_case_db_connection()
            if not conn:
                return server_error_response(message='数据库连接失败')
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

            logger.info(f"工单状态更新: {ticket_id} -> {new_status}")
            return success_response(message='工单状态更新成功')
        except Exception as e:
            log_exception(logger, "更新工单状态失败")
            return server_error_response(message=f'更新失败：{str(e)}')

    @app.route('/case/api/ticket/<ticket_id>/messages', methods=['GET'])
    def case_get_messages(ticket_id):
        """获取工单消息"""
        try:
            log_request(logger, request, f'/case/api/ticket/{ticket_id}/messages')
            conn = get_case_db_connection()
            if not conn:
                return server_error_response(message='数据库连接失败')
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
            log_exception(logger, "查询工单消息失败")
            return server_error_response(message=f'查询失败：{str(e)}')

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
            log_request(logger, request, '/unified/api/users')
            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response(message='数据库连接失败')

            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM `users` ORDER BY created_at DESC")
            users = cursor.fetchall()
            cursor.close()
            conn.close()

            return success_response(data=users, message='获取用户列表成功')
        except Exception as e:
            log_exception(logger, "获取用户列表失败")
            return server_error_response(message=f'获取用户列表失败：{str(e)}')

    @app.route('/unified/api/users', methods=['POST'])
    @login_required(roles=['admin'])
    def unified_add_user():
        """添加统一用户"""
        try:
            log_request(logger, request, '/unified/api/users')
            data = request.get_json()

            if not data.get('username'):
                return error_response(message='用户名不能为空')
            if not data.get('password'):
                return error_response(message='密码不能为空')

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
                logger.info(f"用户创建成功: {data['username']}")
                return success_response(message=message)
            else:
                return error_response(message=message)
        except Exception as e:
            log_exception(logger, "添加用户失败")
            return server_error_response(message=f'添加用户失败：{str(e)}')

    @app.route('/unified/api/users/<int:user_id>', methods=['PUT'])
    @login_required(roles=['admin'])
    def unified_update_user(user_id):
        """更新统一用户"""
        try:
            log_request(logger, request, f'/unified/api/users/{user_id}')
            data = request.get_json()

            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response(message='数据库连接失败')

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

            logger.info(f"用户更新成功: {user_id}")
            return success_response(message='用户更新成功')
        except Exception as e:
            log_exception(logger, "更新用户失败")
            return server_error_response(message=f'更新用户失败：{str(e)}')

    @app.route('/unified/api/users/<int:user_id>', methods=['DELETE'])
    @login_required(roles=['admin'])
    def unified_delete_user(user_id):
        """删除统一用户"""
        try:
            log_request(logger, request, f'/unified/api/users/{user_id}')
            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response(message='数据库连接失败')

            cursor = conn.cursor()

            # 检查是否是当前登录用户
            cursor.execute("SELECT username FROM `users` WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user and user[0] == session.get('username'):
                cursor.close()
                conn.close()
                return error_response(message='不能删除当前登录用户')

            cursor.execute("DELETE FROM `users` WHERE id = %s", (user_id,))
            conn.commit()

            cursor.close()
            conn.close()

            logger.info(f"用户删除成功: {user_id}")
            return success_response(message='用户删除成功')
        except Exception as e:
            log_exception(logger, "删除用户失败")
            return server_error_response(message=f'删除用户失败：{str(e)}')

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
            log_request(logger, request, '/unified/api/case-users')
            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response(message='数据库连接失败')

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

            return success_response(data=users, message='获取用户列表成功')
        except Exception as e:
            log_exception(logger, "获取工单系统用户列表失败")
            return server_error_response(message=f'获取用户列表失败：{str(e)}')

    @app.route('/unified/api/case-users', methods=['POST'])
    @login_required(roles=['admin'])
    def unified_add_case_user():
        """添加工单系统用户"""
        try:
            log_request(logger, request, '/unified/api/case-users')
            data = request.get_json()

            if not data.get('username'):
                return error_response(message='用户名不能为空')
            if not data.get('password'):
                return error_response(message='密码不能为空')
            if not data.get('email'):
                return error_response(message='邮箱不能为空')

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
                logger.info(f"工单系统用户创建成功: {data['username']}")
                return success_response(message=message)
            else:
                return error_response(message=message)
        except Exception as e:
            log_exception(logger, "添加工单系统用户失败")
            return server_error_response(message=f'添加用户失败：{str(e)}')

    @app.route('/unified/api/case-users/<int:user_id>', methods=['PUT'])
    @login_required(roles=['admin'])
    def unified_update_case_user(user_id):
        """更新工单系统用户"""
        try:
            log_request(logger, request, f'/unified/api/case-users/{user_id}')
            data = request.get_json()

            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response(message='数据库连接失败')

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

            logger.info(f"工单系统用户更新成功: {user_id}")
            return success_response(message='用户更新成功')
        except Exception as e:
            log_exception(logger, "更新工单系统用户失败")
            return server_error_response(message=f'更新用户失败：{str(e)}')

    @app.route('/unified/api/case-users/<int:user_id>', methods=['DELETE'])
    @login_required(roles=['admin'])
    def unified_delete_case_user(user_id):
        """删除工单系统用户"""
        try:
            log_request(logger, request, f'/unified/api/case-users/{user_id}')
            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response(message='数据库连接失败')

            cursor = conn.cursor()

            # 检查是否是当前登录用户
            cursor.execute("SELECT username FROM `users` WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user and user[0] == session.get('username'):
                cursor.close()
                conn.close()
                return error_response(message='不能删除当前登录用户')

            cursor.execute("DELETE FROM `users` WHERE id = %s", (user_id,))
            conn.commit()

            cursor.close()
            conn.close()

            logger.info(f"工单系统用户删除成功: {user_id}")
            return success_response(message='用户删除成功')
        except Exception as e:
            log_exception(logger, "删除工单系统用户失败")
            return server_error_response(message=f'删除用户失败：{str(e)}')

    # 用户统计API
    @app.route('/unified/api/user-stats', methods=['GET'])
    @login_required(roles=['admin'])
    def unified_get_user_stats():
        """获取用户统计信息"""
        try:
            log_request(logger, request, '/unified/api/user-stats')
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

            return success_response(data=stats, message='获取统计信息成功')
        except Exception as e:
            log_exception(logger, "获取统计信息失败")
            return server_error_response(message=f'获取统计信息失败：{str(e)}')

    # 管理员重置用户密码路由
    @app.route('/auth/api/reset-password/<int:user_id>', methods=['POST'])
    @login_required(roles=['admin'])
    def reset_user_password(user_id):
        """管理员重置指定用户的密码"""
        try:
            log_request(logger, request, f'/auth/api/reset-password/{user_id}')
            conn = get_unified_kb_conn()
            if not conn:
                return server_error_response(message='数据库连接失败')

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
                return error_response(message='不能重置admin用户密码')

            data = request.get_json()
            new_password = data.get('password', '').strip()

            if not new_password:
                return error_response(message='请输入新密码')

            if len(new_password) < 6:
                return error_response(message='密码长度至少为6位')

            # 生成新的 werkzeug 密码哈希
            password_hash = generate_password_hash(new_password)

            update_sql = "UPDATE `users` SET password_hash = %s, password_type = %s, updated_at = NOW() WHERE id = %s"
            cursor.execute(update_sql, (password_hash, 'werkzeug', user_id))
            conn.commit()

            cursor.close()
            conn.close()

            logger.info(f"管理员重置用户密码成功: {username}")
            return success_response(message=f'用户 {username} 的密码已重置')
        except Exception as e:
            log_exception(logger, "重置用户密码失败")
            return server_error_response(message=f'重置密码失败：{str(e)}')


# ==================== SocketIO事件注册 ====================
def register_socketio_events(socketio):
    """注册SocketIO事件"""

    @socketio.on('connect')
    def handle_connect():
        logger.info(f'客户端已连接：{request.sid}')

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f'客户端已断开连接：{request.sid}')

    @socketio.on('join_ticket')
    def handle_join_ticket(data):
        ticket_id = data.get('ticket_id')
        user_type = data.get('user_type')
        user_name = data.get('user_name', '匿名用户')

        if ticket_id:
            room = f'ticket_{ticket_id}'
            join_room(room)
            logger.info(f'{user_name} ({user_type}) 加入了工单 {ticket_id} 聊天室')

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
            logger.info(f'{user_name} ({user_type}) 离开了工单 {ticket_id} 聊天室')

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

            logger.info(f"工单 {ticket_id} 新消息: {sender_name}")
            return {'success': True, 'message': '消息发送成功'}
        except Exception as e:
            logger.error(f"发送消息异常：{e}")
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
        logger.info("工单系统数据库表初始化成功")
    except pymysql.MySQLError as e:
        conn.rollback()
        logger.error(f"工单系统数据库初始化失败：{e}")
    finally:
        cursor.close()
        conn.close()
