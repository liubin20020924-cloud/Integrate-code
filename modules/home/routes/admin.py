"""
管理后台路由
"""
from flask import Blueprint, render_template

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/messages')
def messages():
    """留言管理"""
    return render_template('messages.html')


@admin_bp.route('/dashboard')
def dashboard():
    """管理仪表板"""
    return render_template('dashboard.html')
