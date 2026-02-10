"""
官网系统路由蓝图
"""
from flask import Blueprint, request, render_template, send_from_directory
from datetime import datetime
import os
from common.response import success_response, error_response, validation_error_response, server_error_response
from common.validators import validate_required, validate_email
from common.logger import logger, log_exception

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def index():
    """官网首页"""
    return render_template('home/index.html', now=datetime.now)


@home_bp.route('/about')
def about():
    """关于我们页面"""
    return render_template('home/about.html', now=datetime.now)


@home_bp.route('/parts')
def parts():
    """备件库页面"""
    return render_template('home/parts.html', now=datetime.now)


@home_bp.route('/cases')
def cases():
    """用户案例页面"""
    return render_template('home/cases.html', now=datetime.now)


@home_bp.route('/jpg/<path:filename>')
def serve_jpg_static(filename):
    """提供官网静态图片文件 - 映射到 static/home/images/"""
    try:
        # 获取项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_dir = os.path.join(base_dir, 'static', 'home', 'images')
        return send_from_directory(image_dir, filename)
    except FileNotFoundError:
        logger.error(f"图片文件不存在: /jpg/{filename}")
        return "404 - Image Not Found", 404
    except Exception as e:
        logger.error(f"静态文件访问错误: {e}")
        return "500 - Internal Server Error", 500


@home_bp.route('/test-images')
def test_images():
    """图片测试页面"""
    return render_template('home_test_images.html')


@home_bp.route('/view-messages')
def view_messages():
    """留言管理页面"""
    return render_template('home/admin_messages.html')


@home_bp.route('/api/contact', methods=['POST'])
def contact():
    """联系表单提交
    
    提交官网联系表单
    ---
    tags:
      - 官网
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        description: 联系表单数据
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - message
          properties:
            name:
              type: string
              description: 联系人姓名
              example: 张三
            email:
              type: string
              format: email
              description: 联系人邮箱
              example: test@example.com
            message:
              type: string
              description: 留言内容
              example: 这是测试消息
    responses:
      200:
        description: 提交成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: 参数错误
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: 服务器错误
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        data = request.get_json()
        
        # 验证必填字段
        is_valid, errors = validate_required(data, ['name', 'email', 'message'])
        if not is_valid:
            return validation_error_response(errors)
        
        # 验证邮箱
        is_valid, msg = validate_email(data['email'])
        if not is_valid:
            return error_response(msg, 400)
        
        logger.info(f"收到联系表单: {data['name']} <{data['email']}>")
        return success_response(message='留言提交成功')
    except Exception as e:
        log_exception(logger, "提交联系表单失败")
        return server_error_response(f'提交失败：{str(e)}')


@home_bp.route('/api/messages', methods=['GET'])
def get_messages():
    """获取留言列表"""
    return success_response(data={'messages': []}, message='查询成功')
