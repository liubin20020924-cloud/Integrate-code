"""
管理后台路由
"""

from flask import Blueprint, render_template, request, redirect, url_for
from models import db, ContactMessage
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/messages')
def messages():
    """留言管理页面（服务器渲染版本）"""
    try:
        # 获取搜索参数
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = 20

        # 构建查询
        query = ContactMessage.query

        # 搜索过滤
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                (ContactMessage.name.like(search_pattern)) |
                (ContactMessage.phone.like(search_pattern)) |
                (ContactMessage.email.like(search_pattern)) |
                (ContactMessage.message.like(search_pattern))
            )

        # 分页
        pagination = query.order_by(ContactMessage.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # 统计总数
        total_count = ContactMessage.query.count()

        return render_template('admin/messages.html',
                             messages=pagination.items,
                             pagination=pagination,
                             search=search,
                             total_count=total_count,
                             now=datetime.now())

    except Exception as e:
        logger.error(f"加载留言管理页面失败: {str(e)}")
        return f"加载失败: {str(e)}", 500
