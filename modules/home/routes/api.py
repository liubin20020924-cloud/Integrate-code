"""
API路由 - 处理API请求
"""
from flask import Blueprint, request, jsonify, redirect, url_for
from datetime import datetime

api_bp = Blueprint('api', __name__)


@api_bp.route('/contact', methods=['POST'])
def contact():
    """联系表单提交"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('name'):
            return jsonify({'success': False, 'message': '请填写姓名'}), 400
        if not data.get('email'):
            return jsonify({'success': False, 'message': '请填写邮箱'}), 400
        if not data.get('message'):
            return jsonify({'success': False, 'message': '请填写留言内容'}), 400

        # TODO: 保存到数据库
        # 这里可以添加数据库保存逻辑

        return jsonify({'success': True, 'message': '留言提交成功'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'提交失败：{str(e)}'}), 500


@api_bp.route('/messages', methods=['GET'])
def get_messages():
    """获取留言列表"""
    # TODO: 从数据库获取留言列表
    return jsonify({
        'success': True,
        'messages': []
    })
