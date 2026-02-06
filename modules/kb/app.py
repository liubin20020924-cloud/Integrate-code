"""
知识库系统应用
"""
from flask import Flask, request
import sys
import os

# 添加项目根目录到路径以导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

# 导入模块
from modules.kb.database.db_utils import init_user_table
from modules.kb.auth.routes import auth_bp
from modules.kb.views.routes import views_bp
from modules.kb.management.routes import management_bp


def create_kb_app():
    """创建知识库Flask应用"""
    # 获取当前文件所在目录的绝对路径
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, '..', '..', 'templates', 'kb')

    app = Flask(__name__, template_folder=template_dir)
    app.secret_key = config.SECRET_KEY
    app.config['JSON_AS_ASCII'] = False

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/kb')
    app.register_blueprint(views_bp, url_prefix='/kb')
    app.register_blueprint(management_bp, url_prefix='/kb')

    # 添加favicon路由
    @app.route('/kb/favicon.ico')
    def favicon():
        from flask import Response
        return Response('', mimetype='image/x-icon')

    # 首页重定向
    @app.route('/kb')
    def kb_index():
        from flask import redirect, url_for
        return redirect(url_for('views.index'))

    @app.route('/kb/MGMT')
    def kb_mgmt():
        from flask import redirect, url_for
        return redirect(url_for('management.management'))

    # 初始化应用
    with app.app_context():
        print("初始化知识库用户表...")
        init_user_table()

    # Edge浏览器优化中间件
    @app.after_request
    def apply_caching(response):
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=3600'
            response.headers['Expires'] = '3600'

        user_agent = request.headers.get('User-Agent', '')
        if 'Edge' in user_agent or 'Trident' in user_agent:
            response.headers['X-UA-Compatible'] = 'IE=edge,chrome=1'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'

            if config.DEBUG_MODE:
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'

        return response

    return app
