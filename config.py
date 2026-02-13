"""
云户科技网站统一配置文件
整合官网、知识库、工单三个系统的配置

配置说明：
1. 所有配置项都在本文件中定义，带默认值
2. 如需修改配置，可直接在本文件中修改
3. 建议根据实际部署环境调整数据库连接、邮件等配置
"""

import os
import secrets
from dotenv import load_dotenv

# 尝试加载 .env 文件（可选，不影响默认配置）
load_dotenv()


# ============================================
# 基础 Flask 配置
# ============================================
class BaseConfig:
    """基础配置类"""
    # Flask 安全密钥 - 生产环境请必须修改！
    # 优先从环境变量读取，否则自动生成随机密钥
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)

    # 调试模式
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'  # 生产环境默认为 False

    # JSON 中文支持
    JSON_AS_ASCII = False

    # Session 配置（已加固）
    SESSION_COOKIE_NAME = 'cloud_doors_session'
    SESSION_COOKIE_SAMESITE = 'Lax'  # HTTPS 后改为 'Strict'
    SESSION_COOKIE_HTTPONLY = True
    # SESSION_COOKIE_SECURE = True  # 启用 HTTPS 后取消注释
    SESSION_COOKIE_MAX_AGE = 10800  # 3 小时
    PERMANENT_SESSION_LIFETIME = 10800  # 3 小时

    # 最大上传大小
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # 静态文件缓存时间
    STATIC_CACHE_TIME = 3600  # 静态文件缓存1小时


# ============================================
# Flask 服务器配置
# ============================================
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')  # 监听所有网卡
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))  # 服务端口

# ============================================
# 网站域名配置
# ============================================
# 网站基础URL（用于生成链接）
SITE_URL = os.getenv('SITE_URL', f'http://{FLASK_HOST}:{FLASK_PORT}')


# ============================================
# 数据库配置 - 统一使用 MariaDB
# ============================================
# 通用数据库配置（三个系统共用）
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', '3306'))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# 数据库密码安全检查
if not DB_PASSWORD:
    import warnings
    warnings.warn(
        "⚠️ 警告: 数据库密码为空！请设置 DB_PASSWORD 环境变量。"
        "生产环境请务必设置数据库密码以确保安全。"
    )

# 各系统数据库名称
DB_NAME_HOME = os.getenv('DB_NAME_HOME', 'clouddoors_db')  # 官网系统数据库
DB_NAME_KB = os.getenv('DB_NAME_KB', 'YHKB')              # 知识库系统数据库
DB_NAME_CASE = os.getenv('DB_NAME_CASE', 'casedb')           # 工单系统数据库

# SQLite 数据库配置（官网系统备用）
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'clouddoors.db')

# 数据库连接池配置（所有系统共用）
DB_POOL_MAX_CONNECTIONS = 20
DB_POOL_MIN_CACHED = 5
DB_POOL_MAX_CACHED = 10
DB_POOL_MAX_SHARED = 5


# ============================================
# 邮件配置
# ============================================
# SMTP 服务器配置（通用）
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.qq.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # 必须从环境变量读取
EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')

# 官网邮件配置（如果使用Gmail）
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
MAIL_USE_TLS = True
MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')  # 如需使用请填写
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')  # 如需使用请填写
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '')

# 联系邮箱
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', '')


# ============================================
# 知识库系统配置
# ============================================
# Trilium 服务器配置
TRILIUM_SERVER_URL = os.getenv('TRILIUM_SERVER_URL', 'http://127.0.0.1:8080')
TRILIUM_TOKEN = os.getenv('TRILIUM_TOKEN', '')  # 必须从环境变量读取
TRILIUM_SERVER_HOST = os.getenv('TRILIUM_SERVER_HOST', '127.0.0.1:8080')

# Trilium 登录配置
TRILIUM_LOGIN_USERNAME = os.getenv('TRILIUM_LOGIN_USERNAME', '')  # 如需认证请填写用户名
TRILIUM_LOGIN_PASSWORD = os.getenv('TRILIUM_LOGIN_PASSWORD', '')

# 知识库登录配置
SESSION_TIMEOUT = 180  # Session超时时间（秒），3小时
DEFAULT_ADMIN_USERNAME = 'admin'

# ⚠️ 安全警告：默认管理员密码（仅在开发环境使用）
# 生产环境请务必通过环境变量 DEFAULT_ADMIN_PASSWORD 设置强密码
DEFAULT_ADMIN_PASSWORD = os.getenv('DEFAULT_ADMIN_PASSWORD', 'YHKB@2024')

# 密码安全检查
if DEFAULT_ADMIN_PASSWORD == 'YHKB@2024' and not os.getenv('DEFAULT_ADMIN_PASSWORD'):
    import warnings
    warnings.warn(
        "⚠️ 警告: 使用默认管理员密码 'YHKB@2024'！"
        "生产环境请立即修改默认密码，设置环境变量 DEFAULT_ADMIN_PASSWORD。"
        "密码要求至少10位，包含大小写字母、数字和特殊字符。"
    )

# 内容查看配置
ENABLE_CONTENT_VIEW = True
CONTENT_CACHE_TIMEOUT = 300  # 内容缓存时间（秒）

# HTML 内容安全配置
ALLOWED_HTML_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'div', 'span',
    'strong', 'b', 'em', 'i', 'u', 's',
    'ul', 'ol', 'li',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'a', 'img',
    'pre', 'code',
    'blockquote', 'hr'
]

ALLOWED_HTML_ATTRIBUTES = {
    '*': ['class', 'style', 'id'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'table': ['border', 'cellpadding', 'cellspacing', 'width'],
}

# 调试配置
DEBUG_MODE = False  # 默认关闭调试模式
DEBUG_ADMIN_ONLY = True  # 调试功能仅管理员可访问

# 图片处理配置
ENABLE_IMAGE_PROXY = True

# 浏览器优化配置
ENABLE_EDGE_OPTIMIZATION = True
EDGE_COMPATIBILITY_MODE = True
CACHE_CONTROL_HEADERS = True


# ============================================
# 路由配置
# ============================================
# 各模块路由前缀
HOME_PREFIX = ''  # 官网系统根路径
KB_PREFIX = '/kb'  # 知识库系统前缀
CASE_PREFIX = '/case'  # 工单系统前缀


# ============================================
# CORS 配置
# ============================================
# 允许的跨域来源（多个来源用逗号分隔）
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*')

# ============================================
# Redis 配置（用于图片缓存）
# ============================================
REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'False').lower() == 'true'
REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# ============================================
# CDN 配置（可选）
# ============================================
CDN_ENABLED = os.getenv('CDN_ENABLED', 'False').lower() == 'true'
CDN_DOMAIN = os.getenv('CDN_DOMAIN', '')
CDN_PROTOCOL = os.getenv('CDN_PROTOCOL', 'https')

# ============================================
# 图片优化配置
# ============================================
IMAGE_QUALITY = int(os.getenv('IMAGE_QUALITY', '80'))
IMAGE_ENABLE_WEBP = os.getenv('IMAGE_ENABLE_WEBP', 'True').lower() == 'true'
IMAGE_AUTO_COMPRESS = os.getenv('IMAGE_AUTO_COMPRESS', 'True').lower() == 'true'
IMAGE_CACHE_TTL = int(os.getenv('IMAGE_CACHE_TTL', '604800'))  # 7天

# ============================================
# 缓存配置
# ============================================
# 缓存类型：redis, simple, filesystem
CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '604800'))  # 7天
CACHE_KEY_PREFIX = os.getenv('CACHE_KEY_PREFIX', 'yundour_')

# ============================================
# 日志配置
# ============================================
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
# 日志文件路径
LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
# 日志文件最大大小（MB）
LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10'))
# 日志文件备份数量
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))


# ============================================
# 配置检查函数
# ============================================
def check_config():
    """检查关键配置项"""
    warnings = []
    errors = []

    # 检查生产环境配置
    if not BaseConfig.DEBUG:
        if BaseConfig.SECRET_KEY == 'yihu-website-secret-key-2024-CHANGE-ME':
            errors.append('严重错误: 生产环境使用了默认SECRET_KEY，请立即修改！设置 FLASK_SECRET_KEY 环境变量')

    # 检查敏感配置是否从环境变量读取
    if not DB_PASSWORD:
        errors.append('严重错误: DB_PASSWORD 未设置，数据库连接将失败')

    if DB_HOST == '127.0.0.1' and not BaseConfig.DEBUG:
        warnings.append('警告: 生产环境数据库地址使用默认值 127.0.0.1，请确认 DB_HOST 配置正确')

    if not SMTP_PASSWORD and not MAIL_PASSWORD:
        errors.append('警告: SMTP_PASSWORD 和 MAIL_PASSWORD 均未设置，邮件功能可能无法使用')

    if SMTP_USERNAME and '@qq.com' in SMTP_USERNAME:
        warnings.append('提示: 邮件配置使用QQ邮箱，确保已配置正确的授权码')

    if not TRILIUM_TOKEN:
        errors.append('严重错误: TRILIUM_TOKEN 未设置，知识库功能将无法使用')

    if not TRILIUM_LOGIN_PASSWORD and TRILIUM_LOGIN_USERNAME:
        warnings.append('警告: TRILIUM_LOGIN_PASSWORD 未设置，Trilium 认证功能可能无法使用')

    if TRILIUM_SERVER_URL == 'http://127.0.0.1:8080' and not BaseConfig.DEBUG:
        warnings.append('警告: 生产环境 Trilium 地址使用默认值，请确认 TRILIUM_SERVER_URL 配置正确')

    # 检查默认管理员密码
    if DEFAULT_ADMIN_PASSWORD == 'YHKB@2024':
        warnings.append('警告: 知识库默认管理员密码未修改，建议立即修改')

    # 检查邮件配置
    if SMTP_USERNAME and '@qq.com' in SMTP_USERNAME:
        warnings.append('提示: 邮件配置使用QQ邮箱，确保已配置正确的授权码')

    # 检查 .env 文件是否存在
    if not os.path.exists('.env'):
        errors.append('严重错误: 未找到 .env 文件，请创建并配置环境变量')

    # 检查 Redis 配置
    if REDIS_ENABLED and REDIS_HOST == '127.0.0.1' and not BaseConfig.DEBUG:
        warnings.append('警告: 生产环境 Redis 地址使用默认值，请确认 REDIS_HOST 配置正确')

    # 检查网站域名配置
    if SITE_URL == 'http://0.0.0.0:5000' and not BaseConfig.DEBUG:
        errors.append('严重错误: 生产环境 SITE_URL 使用默认值，请设置为实际网站域名')

    # 检查 CDN 配置
    if CDN_ENABLED and not CDN_DOMAIN:
        errors.append('严重错误: CDN_ENABLED 为 True 但未设置 CDN_DOMAIN')

    return warnings, errors



# 启动时自动检查配置
if __name__ != '__main__':
    config_warnings, config_errors = check_config()
    if config_warnings or config_errors:
        print("=" * 60)
        print("配置检查结果:")
        if config_errors:
            print("\n【严重错误】:")
            for error in config_errors:
                print(f"  [X] {error}")
        if config_warnings:
            print("\n【警告提示】:")
            for warning in config_warnings:
                print(f"  [!] {warning}")
        print("=" * 60)
        if config_errors:
            print("\n注意：存在严重配置错误，建议立即修复！\n")
    else:
        print("=" * 60)
        print("配置检查通过 [OK]")
        print("=" * 60)
