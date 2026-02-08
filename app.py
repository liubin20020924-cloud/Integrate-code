"""
云户科技网站 - 统一主入口
整合官网、知识库、工单三个系统
使用统一路由管理
"""
from flask import Flask, make_response, request
from flask_socketio import SocketIO
import jinja2
import config
from common.db_manager import get_pool
from routes import register_all_routes, register_socketio_events, init_case_database
import os
from datetime import timedelta

# 初始化主应用
import os
template_dirs = [
    os.path.join(os.path.dirname(__file__), 'templates')
]
app = Flask(__name__, template_folder='templates')
app.jinja_loader = jinja2.ChoiceLoader([jinja2.FileSystemLoader(d) for d in template_dirs])
app.secret_key = config.BaseConfig.SECRET_KEY
app.config['JSON_AS_ASCII'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['DEBUG'] = config.BaseConfig.DEBUG

# 性能优化配置
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=3)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = config.BaseConfig.STATIC_CACHE_TIME

# 初始化SocketIO
try:
    import eventlet
    eventlet.monkey_patch()
    async_mode = 'eventlet'
except ImportError:
    try:
        import gevent
        import gevent.monkey
        gevent.monkey.patch_all()
        async_mode = 'gevent'
    except ImportError:
        async_mode = 'threading'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode)

# 预热数据库连接池
print("预热数据库连接池...")
for db_name in ['home', 'kb', 'case']:
    _ = get_pool(db_name)
print("数据库连接池初始化完成")

# 静态文件优化 - 添加缓存头
@app.after_request
def add_cache_headers(response):
    """为静态资源添加缓存头"""
    # 静态文件缓存
    if request.path.startswith('/static/'):
        response.cache_control.max_age = config.BaseConfig.STATIC_CACHE_TIME
        response.cache_control.public = True
        response.headers['Cache-Control'] = f'public, max-age={config.BaseConfig.STATIC_CACHE_TIME}'
    # API响应不缓存
    elif request.path.startswith('/kb/api/') or request.path.startswith('/auth/api/') or request.path.startswith('/unified/api/'):
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# 初始化工单系统数据库
print("初始化工单系统数据库...")
init_case_database()

# 注册所有路由
print("注册路由系统...")
register_all_routes(app)

# 注册SocketIO事件
register_socketio_events(socketio)

print("=" * 60)
print("云户科技网站启动完成")
print("=" * 60)
print(f"官网首页: http://{config.FLASK_HOST}:{config.FLASK_PORT}/")
print(f"知识库系统: http://{config.FLASK_HOST}:{config.FLASK_PORT}/kb")
print(f"工单系统: http://{config.FLASK_HOST}:{config.FLASK_PORT}/case")
print(f"统一用户管理: http://{config.FLASK_HOST}:{config.FLASK_PORT}/unified/users")
print("=" * 60)


if __name__ == '__main__':
    # 使用socketio.run以支持WebSocket
    socketio.run(app, host=config.FLASK_HOST, port=config.FLASK_PORT,
                 debug=config.BaseConfig.DEBUG, allow_unsafe_werkzeug=True)
