"""
API路由 - 处理表单提交等API请求
"""

from flask import Blueprint, request, jsonify, current_app
from models import db, ContactMessage
from validators import validate_contact_form, sanitize_input
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


@api_bp.route('/submit-form', methods=['POST'])
def submit_form():
    """
    提交联系表单
    """
    try:
        # 获取表单数据
        data = {
            'name': request.form.get('name', ''),
            'phone': request.form.get('phone', ''),
            'email': request.form.get('email', ''),
            'message': request.form.get('message', '')
        }

        # 验证表单
        is_valid, errors = validate_contact_form(data)

        if not is_valid:
            return jsonify({
                'success': False,
                'message': '<br>'.join(errors),
                'code': 'validation_error'
            }), 400

        # 过滤输入
        name = sanitize_input(data['name'])
        phone = sanitize_input(data['phone'])
        email = sanitize_input(data['email']) if data['email'] else None
        message = sanitize_input(data['message'])

        # 创建新留言
        contact_msg = ContactMessage(
            name=name,
            phone=phone,
            email=email,
            message=message,
            status=1
        )

        # 保存到数据库
        db.session.add(contact_msg)
        db.session.commit()

        # 获取新插入的ID
        message_id = contact_msg.id

        logger.info(f"新留言提交成功 - ID: {message_id}, 姓名: {name}, 电话: {phone}")

        # 返回成功响应
        return jsonify({
            'success': True,
            'message': f'提交成功！您的留言ID是：{message_id}，我们会尽快与您联系。',
            'message_id': message_id
        })

    except Exception as e:
        logger.error(f"表单提交失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '提交失败，请稍后重试。',
            'code': 'server_error'
        }), 500


@api_bp.route('/messages', methods=['GET'])
def get_messages():
    """
    获取留言列表（带搜索和分页）
    """
    try:
        # 获取参数
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

        # 返回结果
        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取留言列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取留言失败',
            'code': 'server_error'
        }), 500


@api_bp.route('/messages/<int:message_id>', methods=['GET'])
def get_message_detail(message_id):
    """
    获取单条留言详情
    """
    try:
        message = ContactMessage.query.get_or_404(message_id)
        return jsonify({
            'success': True,
            'message': message.to_dict()
        })

    except Exception as e:
        logger.error(f"获取留言详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取留言详情失败',
            'code': 'server_error'
        }), 404


@api_bp.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """
    删除留言
    """
    try:
        message = ContactMessage.query.get_or_404(message_id)
        db.session.delete(message)
        db.session.commit()

        logger.info(f"留言删除成功 - ID: {message_id}")
        return jsonify({
            'success': True,
            'message': '删除成功'
        })

    except Exception as e:
        logger.error(f"删除留言失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '删除失败',
            'code': 'server_error'
        }), 500


@api_bp.route('/messages/<int:message_id>/status', methods=['PUT'])
def update_message_status(message_id):
    """
    更新留言状态
    """
    try:
        data = request.get_json()
        new_status = data.get('status')

        if new_status not in [1, 2, 3]:
            return jsonify({
                'success': False,
                'message': '无效的状态值'
            }), 400

        message = ContactMessage.query.get_or_404(message_id)
        message.status = new_status
        db.session.commit()

        logger.info(f"留言状态更新成功 - ID: {message_id}, 状态: {new_status}")
        return jsonify({
            'success': True,
            'message': '状态更新成功'
        })

    except Exception as e:
        logger.error(f"更新留言状态失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '更新失败',
            'code': 'server_error'
        }), 500
