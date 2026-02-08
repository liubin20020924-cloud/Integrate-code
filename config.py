"""
云户科技网站统一配置文件
整合官网、知识库、工单三个系统的配置

配置说明：
1. 所有配置项都在本文件中定义，带默认值
2. 如需修改配置，可直接在本文件中修改
3. 建议根据实际部署环境调整数据库连接、邮件等配置
"""

import os
from dotenv import load_dotenv

# 尝试加载 .env 文件（可选，不影响默认配置）
load_dotenv()


# ============================================
# 基础 Flask 配置
# ============================================
class BaseConfig:
    """基础配置类"""
    # Flask 安全密钥 - 生产环境请修改
    SECRET_KEY = 'yihu-website-secret-key-2024-CHANGE-ME'

    # 调试模式
    DEBUG = True  # 生产环境设置为 False

    # JSON 中文支持
    JSON_AS_ASCII = False

    # Session 配置
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_HTTPONLY = True

    # 最大上传大小
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB


# ============================================
# Flask 服务器配置
# ============================================
FLASK_HOST = '0.0.0.0'  # 监听所有网卡
FLASK_PORT = 5000  # 服务端口


# ============================================
# 数据库配置 - 统一使用 MariaDB
# ============================================
# 通用数据库配置（三个系统共用）
DB_HOST = '10.10.10.250'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = 'Nutanix/4u123!'

# 各系统数据库名称
DB_NAME_HOME = 'clouddoors_db'  # 官网系统数据库
DB_NAME_KB = 'YHKB'              # 知识库系统数据库
DB_NAME_CASE = 'casedb'           # 工单系统数据库

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
SMTP_SERVER = 'smtp.qq.com'
SMTP_PORT = 465
SMTP_USERNAME = '1919516011@qq.com'
SMTP_PASSWORD = 'xrbvyjjfkpdmcfbj'  # QQ邮箱授权码
EMAIL_SENDER = '1919516011@qq.com'

# 官网邮件配置（如果使用Gmail）
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = ''  # 如需使用请填写
MAIL_PASSWORD = ''  # 如需使用请填写
MAIL_DEFAULT_SENDER = 'noreply@cloud-doors.com'

# 联系邮箱
CONTACT_EMAIL = 'dora.dong@cloud-doors.com'


# ============================================
# 知识库系统配置
# ============================================
# Trilium 服务器配置
TRILIUM_SERVER_URL = 'http://10.10.10.250:8080'
TRILIUM_TOKEN = 'geJWc61h07w7_OSwK2FqHZ4PaV3F8K8iCx/Rus2EaIJn1uyNyrRM6zOk='
TRILIUM_SERVER_HOST = '10.10.10.250:8080'

# Trilium 登录配置
TRILIUM_LOGIN_USERNAME = ''  # 如需认证请填写用户名
TRILIUM_LOGIN_PASSWORD = 'Nutanix/4u123!'

# 知识库登录配置
SESSION_TIMEOUT = 180  # Session超时时间（秒），3小时
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'YHKB@2024'

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
STATIC_CACHE_TIME = 3600  # 静态文件缓存1小时


# ============================================
# 路由配置
# ============================================
# 各模块路由前缀
HOME_PREFIX = ''  # 官网系统根路径
KB_PREFIX = '/kb'  # 知识库系统前缀
CASE_PREFIX = '/case'  # 工单系统前缀


# ============================================
# 配置检查函数
# ============================================
def check_config():
    """检查关键配置项"""
    warnings = []

    # 检查生产环境配置
    if not BaseConfig.DEBUG:
        if BaseConfig.SECRET_KEY == 'yihu-website-secret-key-2024-CHANGE-ME':
            warnings.append('警告: 生产环境使用了默认SECRET_KEY，请修改！')

    # 检查数据库配置
    if not DB_PASSWORD or DB_PASSWORD == 'Nutanix/4u123!':
        warnings.append('提示: 数据库密码使用默认值，建议修改')

    # 检查邮件配置
    if SMTP_USERNAME and '@qq.com' in SMTP_USERNAME:
        warnings.append('提示: 邮件配置使用QQ邮箱，确保已配置正确的授权码')

    return warnings



# 启动时自动检查配置
if __name__ != '__main__':
    config_warnings = check_config()
    if config_warnings:
        print("=" * 60)
        print("配置检查结果:")
        for warning in config_warnings:
            print(f"  {warning}")
        print("=" * 60)
