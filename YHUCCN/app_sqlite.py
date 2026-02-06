"""
云户科技网站 - Flask 应用 (SQLite版 - 用于快速测试)
"""

from flask import Flask, jsonify, request, send_from_directory
from config_sqlite import Config
from models import db
from datetime import datetime
import os

def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # 加载配置
    app.config.from_object(config_class)

    # 初始化数据库
    db.init_app(app)

    # 注册蓝图
    from routes.main import main_bp
    from routes.api import api_bp
    from routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # 处理jpg文件夹作为静态文件
    @app.route('/jpg/<path:filename>')
    def serve_jpg(filename):
        return send_from_directory('jpg', filename)

    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        if request.is_json:
            return jsonify({'error': 'Not found', 'code': 404}), 404
        return "Page not found", 404

    @app.errorhandler(500)
    def internal_error(error):
        if request.is_json:
            return jsonify({'error': 'Internal server error', 'code': 500}), 500
        return "Internal server error", 500

    # 模板上下文处理器
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    return app


if __name__ == '__main__':
    app = create_app()
    print("云户科技网站启动中 (SQLite版本)...")
    print("访问地址: http://localhost:5000")
    print("说明: 此版本使用SQLite数据库，无需配置MySQL，适合快速测试")
    app.run(host='0.0.0.0', port=5000, debug=True)
