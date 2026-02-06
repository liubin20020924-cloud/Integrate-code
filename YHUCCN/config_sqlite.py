import os

class Config:
    """SQLite配置 - 用于测试"""

    SECRET_KEY = 'dev-secret-key-change-in-production'
    DEBUG = True

    # 使用SQLite数据库（无需配置MySQL）
    SQLALCHEMY_DATABASE_URI = 'sqlite:///clouddoors.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # 上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # 联系邮箱
    CONTACT_EMAIL = 'dora.dong@cloud-doors.com'
