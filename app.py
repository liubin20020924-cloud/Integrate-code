"""
云户科技网站 - 统一主入口
整合官网、知识库、工单三个系统
"""
from flask import Flask, redirect, url_for, session
from flask_socketio import SocketIO
import config
from common.db_manager import get_pool  # 预热连接池

# 初始化主应用
app = Flask(__name__)
app.secret_key = config.BaseConfig.SECRET_KEY
app.config['JSON_AS_ASCII'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['DEBUG'] = config.BaseConfig.DEBUG


# 初始化SocketIO（用于工单系统WebSocket）
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 预热所有数据库连接池
print("预热数据库连接池...")
for db_name in ['home', 'kb', 'case']:
    _ = get_pool(db_name)
print("数据库连接池初始化完成")

# 注册各模块蓝图
# 1. 工单系统
from modules.case.routes import case_bp, init_database, register_socketio_events
app.register_blueprint(case_bp)

# 注册SocketIO事件
register_socketio_events(socketio)

# 初始化工单系统数据库
print("初始化工单系统数据库...")
init_database()

# 2. 知识库系统
from modules.kb.app import create_kb_app
kb_app = create_kb_app()
# 将知识库蓝图注册到主应用
with kb_app.app_context():
    print("知识库系统已加载")

# 将知识库的所有路由注册到主应用
for rule in kb_app.url_map.iter_rules():
    if rule.endpoint != 'static':
        # 添加前缀 kb/
        route_prefix = f'/kb{rule.rule}'
        # 导出路由函数
        view_func = kb_app.view_functions[rule.endpoint]
        # 注册到主应用
        app.add_url_rule(route_prefix, rule.endpoint, view_func, methods=rule.methods)

# 3. 官网系统
from modules.home.app import create_home_app
home_app = create_home_app()
# 将官网的所有路由注册到主应用
with home_app.app_context():
    print("官网系统已加载")

for rule in home_app.url_map.iter_rules():
    if rule.endpoint != 'static':
        view_func = home_app.view_functions[rule.endpoint]
        # 直接注册，不添加前缀（官网在根路径）
        app.add_url_rule(rule.rule, rule.endpoint, view_func, methods=rule.methods)

# 4. 统一用户管理
from modules.unified.routes import unified_bp
app.register_blueprint(unified_bp)
print("统一用户管理模块已加载")


# 全局会话管理中间件
@app.before_request
def before_request():
    """请求前处理"""
    # 设置会话为永不过期（由浏览器关闭决定）
    session.permanent = False


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    if error:
        return "404 - Page Not Found", 404
    return redirect(url_for('main.index'))


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return "500 - Internal Server Error", 500


# 根路径重定向到官网首页
@app.route('/favicon.ico')
def favicon():
    """返回空的favicon"""
    from flask import Response
    return Response('', mimetype='image/x-icon')


if __name__ == '__main__':
    print("=" * 60)
    print("云户科技网站启动中...")
    print("=" * 60)
    print(f"官网首页: http://{config.FLASK_HOST}:{config.FLASK_PORT}/")
    print(f"知识库系统: http://{config.FLASK_HOST}:{config.FLASK_PORT}/kb")
    print(f"工单系统: http://{config.FLASK_HOST}:{config.FLASK_PORT}/case")
    print(f"统一用户管理: http://{config.FLASK_HOST}:{config.FLASK_PORT}/unified/users")
    print("=" * 60)

    # 使用socketio.run以支持WebSocket
    socketio.run(app, host=config.FLASK_HOST, port=config.FLASK_PORT,
                 debug=config.BaseConfig.DEBUG, allow_unsafe_werkzeug=True)
