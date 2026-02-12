"""
知识库系统路由蓝图 - 认证和浏览
"""
from flask import Blueprint, request, redirect, url_for, session, render_template, Response
from datetime import datetime
import requests
from common.unified_auth import get_current_user, login_required
from common.logger import logger
from common.kb_utils import (
    fetch_all_records, fetch_record_by_id, fetch_records_by_name_with_pagination,
    get_total_count, fetch_records_with_pagination, get_kb_db_connection
)
import config

kb_bp = Blueprint('kb', __name__, url_prefix='/kb')


@kb_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    """知识库系统登录
    
    用户登录知识库系统
    ---
    tags:
      - 知识库-认证
    consumes:
      - application/x-www-form-urlencoded
    parameters:
      - in: formData
        name: username
        type: string
        required: true
        description: 用户名或邮箱
      - in: formData
        name: password
        type: string
        required: true
        description: 密码
    responses:
      200:
        description: 登录成功，重定向到知识库首页
      302:
        description: 已登录，重定向到知识库首页
    """
    user = get_current_user()
    if user:
        logger.info("用户已登录，重定向到知识库首页")
        return redirect(url_for('kb.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template('kb/login.html', error="请输入用户名和密码")
        
        from common.unified_auth import authenticate_user
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
            return redirect(url_for('kb.index'))
        else:
            logger.warning(f"用户 {username} 登录失败: {result}")
            return render_template('kb/login.html', error=result, username=username)
    
    return render_template('kb/login.html')


@kb_bp.route('/auth/logout')
def logout():
    """退出登录"""
    username = session.get('username', 'unknown')
    session.clear()
    logger.info(f"用户 {username} 退出登录")
    return redirect(url_for('kb.login'))


@kb_bp.route('/auth/check-login')
def check_login():
    """检查登录状态"""
    user = get_current_user()
    if user:
        from common.response import success_response
        return success_response(data={'user': user}, message='已登录')
    from common.response import unauthorized_response
    return unauthorized_response(message='未登录')


@kb_bp.route('/')
@login_required()
def index():
    """知识库首页"""
    user = get_current_user()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 15
        records, total_count = fetch_records_with_pagination(page, per_page)
        total_pages = (total_count + per_page - 1) // per_page
        showing_start = (page - 1) * per_page + 1
        showing_end = min(page * per_page, total_count)

        # 获取Trilium基础URL
        trilium_base_url = getattr(config, 'TRILIUM_SERVER_URL', '').rstrip('/')

        return render_template('kb/index.html', records=records,
                             total_count=total_count,
                             showing_count=showing_end - showing_start + 1 if records else 0,
                             page=page,
                             per_page=per_page,
                             total_pages=total_pages,
                             showing_start=showing_start,
                             showing_end=showing_end,
                             is_search=False,
                             current_user=user,
                             trilium_base_url=trilium_base_url)
    except Exception as e:
        from common.response import error_response
        logger.error(f"加载知识库首页失败: {e}")

        # 获取Trilium基础URL
        trilium_base_url = getattr(config, 'TRILIUM_SERVER_URL', '').rstrip('/')

        return render_template('kb/index.html', records=[],
                             error=str(e),
                             total_count=0,
                             showing_count=0,
                             page=1,
                             per_page=15,
                             total_pages=1,
                             is_search=False,
                             current_user=user,
                             trilium_base_url=trilium_base_url)


@kb_bp.route('/search', methods=['GET'])
@login_required()
def search():
    """搜索知识库"""
    search_id = request.args.get('id', '').strip()
    page = request.args.get('page', 1, type=int)

    # 获取Trilium基础URL
    trilium_base_url = getattr(config, 'TRILIUM_SERVER_URL', '').rstrip('/')

    if not search_id:
        return render_template('kb/index.html', records=[],
                             error="请输入搜索ID",
                             total_count=get_total_count(),
                             showing_count=0,
                             page=1,
                             per_page=15,
                             total_pages=1,
                             is_search=True,
                             search_id="",
                             trilium_base_url=trilium_base_url)

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
                                 is_search=True,
                                 trilium_base_url=trilium_base_url)
        else:
            return render_template('kb/index.html', records=[],
                                 error=f"未找到ID为 {search_id} 的记录",
                                 total_count=get_total_count(),
                                 showing_count=0,
                                 page=1,
                                 per_page=15,
                                 total_pages=1,
                                 search_id=search_id,
                                 is_search=True,
                                 trilium_base_url=trilium_base_url)
    except ValueError:
        return render_template('kb/index.html', records=[],
                             error="请输入有效的数字ID",
                             total_count=get_total_count(),
                             showing_count=0,
                             page=1,
                             per_page=15,
                             total_pages=1,
                             search_id=search_id,
                             is_search=True,
                             trilium_base_url=trilium_base_url)


@kb_bp.route('/api/all')
@login_required()
def get_all():
    """获取所有数据"""
    try:
        records = fetch_all_records()
        from common.response import success_response
        return success_response(data={'records': records, 'count': len(records)}, message='查询成功')
    except Exception as e:
        from common.response import server_error_response
        from common.logger import log_exception
        log_exception(logger, "获取所有知识库记录失败")
        return server_error_response(f"数据库错误: {str(e)}")


@kb_bp.route('/search/name', methods=['POST'])
@login_required()
def search_by_name():
    """按名称搜索"""
    name = request.form.get('name', '').strip()
    page = request.form.get('page', 1, type=int)
    per_page = request.form.get('per_page', 15, type=int)
    
    if not name:
        from common.response import error_response
        return error_response('请输入知识库名称', 400)
    
    try:
        records, total_count = fetch_records_by_name_with_pagination(name, page, per_page)
        total_pages = (total_count + per_page - 1) // per_page
        from common.response import success_response
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
        from common.response import server_error_response
        from common.logger import log_exception
        log_exception(logger, "按名称搜索知识库记录失败")
        return server_error_response(f"搜索错误: {str(e)}")


@kb_bp.route('/api/stats')
@login_required()
def get_stats():
    """统计信息"""
    try:
        count = get_total_count()
        from common.response import success_response
        return success_response(data={'total_count': count}, message='查询成功')
    except Exception as e:
        from common.response import server_error_response
        from common.logger import log_exception
        log_exception(logger, "获取知识库统计信息失败")
        return server_error_response(f"统计信息获取失败: {str(e)}")


@kb_bp.route('/api/attachments/<path:attachment_path>')
def proxy_trilium_attachment(attachment_path):
    """代理 Trilium 附件请求，使用 ETAPI

    将前端请求的 Trilium 附件代理转发到 Trilium 服务器
    ---
    tags:
      - Trilium
    parameters:
      - name: attachment_path
        in: path
        type: string
        required: true
        description: 附件路径 (格式: ZjD0OZLY4aWU/image/f6f83bfe35c1711a70ed62a985ab1a92.png)
    responses:
      200:
        description: 附件内容
      404:
        description: 附件未找到
      500:
        description: 服务器错误
    """
    try:
        # 检查 Trilium 配置
        if not hasattr(config, 'TRILIUM_SERVER_URL') or not config.TRILIUM_SERVER_URL:
            logger.error("Trilium 服务未配置")
            from common.response import error_response
            return error_response('Trilium 服务未配置', 500)

        # attachment_path 格式: ZjD0OZLY4aWU/image/f6f83bfe35c1711a70ed62a985ab1a92.png
        # 提取 attachment_id (第一部分)
        parts = attachment_path.split('/')
        if not parts or len(parts) < 1:
            return Response('Invalid attachment path', status=400)

        attachment_id = parts[0]
        logger.info(f"代理 Trilium 附件: attachment_id={attachment_id}, full_path={attachment_path}")

        # 使用 trilium-py 的 ETAPI 获取附件内容
        from trilium_py.client import ETAPI
        server_url = config.TRILIUM_SERVER_URL.rstrip('/')

        # 如果没有token，尝试使用密码登录
        token = config.TRILIUM_TOKEN
        if not token and hasattr(config, 'TRILIUM_LOGIN_PASSWORD'):
            ea = ETAPI(server_url)
            token = ea.login(config.TRILIUM_LOGIN_PASSWORD)
            logger.info("使用密码登录Trilium成功")
            if not token:
                from common.response import error_response
                return error_response('Trilium登录失败，请检查密码配置', 500)

        ea = ETAPI(server_url, token)

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
            logger.error(f"从 Trilium 获取附件失败: attachment_id={attachment_id}")
            return Response('Attachment not found', status=404)

    except Exception as e:
        logger.error(f"代理 Trilium 附件失败: {str(e)}")
        return Response(f'Failed to proxy attachment: {str(e)}', status=500)


@kb_bp.route('/auth/users')
@login_required(roles=['admin'])
def user_management():
    """用户管理页面"""
    try:
        from common.database_context import db_connection
        from common.logger import log_exception

        with db_connection('kb') as conn:
            cursor = conn.cursor()

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

            return render_template('kb/user_management.html', users=users,
                                 login_logs=login_logs,
                                 total_count=len(users) if users else 0)
    except Exception as e:
        from common.logger import log_exception
        log_exception(logger, "加载知识库用户管理页面失败")
        return render_template('kb/user_management.html', users=[],
                             login_logs=[],
                             error=str(e),
                             total_count=0)




