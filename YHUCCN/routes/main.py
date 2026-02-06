"""
主路由 - 处理首页和各页面组件
"""

from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
import os

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """首页 - 组合所有组件"""
    return render_template('index.html', now=datetime.now())


@main_bp.route('/test-images')
def test_images():
    """图片测试页面"""
    return render_template('test_images.html')


@main_bp.route('/view-messages')
def view_messages():
    """留言管理页面"""
    return render_template('view_messages.html')
