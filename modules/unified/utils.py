"""
统一用户管理工具模块
"""
from flask import session, request, redirect, url_for, jsonify
from functools import wraps
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common.db_manager import get_connection
import pymysql


def get_current_user():
    """获取当前登录用户信息"""
    user_id = session.get('user_id')
    if not user_id:
        return None

    try:
        connection = get_connection('kb')
        if connection is None:
            return None

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT id, username, display_name, role, status, last_login
                FROM mgmt_users
                WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()

        connection.close()
        return user

    except Exception as e:
        print(f"获取当前用户失败: {e}")
        return None


def login_required(roles=None):
    """登录验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.is_json:
                    return jsonify({'success': False, 'message': '未登录'}), 401
                return redirect(url_for('kb.auth.login'))

            if roles and user.get('role') not in roles:
                if request.is_json:
                    return jsonify({'success': False, 'message': '权限不足'}), 403
                return redirect(url_for('kb.auth.login'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
