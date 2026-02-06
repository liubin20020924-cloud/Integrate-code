"""
官网系统应用
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sys
import os

# 添加项目根目录到路径以导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

db = SQLAlchemy()


def create_home_app():
    """创建官网Flask应用"""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, '..', '..', 'templates', 'home')
    static_dir = os.path.join(base_dir, '..', '..', 'static', 'home', 'images')

    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)

    # 加载配置
    app.config.from_object(BaseConfig)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME_HOME}?charset=utf8mb4"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = False

    # 初始化数据库
    db.init_app(app)

    # 注册蓝图
    from modules.home.routes.main import main_bp
    from modules.home.routes.api import api_bp
    from modules.home.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # 处理jpg文件夹作为静态文件
    @app.route('/jpg/<path:filename>')
    def serve_jpg(filename):
        return send_from_directory(static_dir, filename)

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


class BaseConfig:
    """基础配置类"""
    SECRET_KEY = config.SECRET_KEY
    DEBUG = config.DEBUG
    JSON_AS_ASCII = False
