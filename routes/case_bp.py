"""
工单系统路由蓝图
"""
from flask import Blueprint, request, render_template, session, jsonify
from common.response import success_response, error_response, unauthorized_response, server_error_response
from common.unified_auth import get_current_user, authenticate_user
from common.validators import validate_email, validate_required, validate_phone
from common.logger import logger, log_request, log_exception
from common.database_context import db_connection
from datetime import datetime
import pymysql

case_bp = Blueprint('case', __name__, url_prefix='/case')


def generate_ticket_id():
    """生成唯一工单ID"""
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    import uuid
    random_str = str(uuid.uuid4())[:6].upper()
    return f"TK-{now}-{random_str}"


@case_bp.route('/')
def index():
    """首页"""
    return render_template('case/login.html')


@case_bp.route('/api/login', methods=['POST'])
def login():
    """工单系统登录
    
    用户登录工单系统
    ---
    tags:
      - 工单-认证
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: 用户名
            password:
              type: string
              description: 密码
    responses:
      200:
        description: 登录成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      401:
        description: 登录失败
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        log_request(logger, request)
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # 简单验证用户名和密码
        if not username:
            return error_response(message='用户名不能为空')
        if not password:
            return error_response(message='密码不能为空')
        
        # 使用统一认证
        success, result = authenticate_user(username, password)
        
        if not success:
            return unauthorized_response(message=result)
        
        user_info = result
        
        session['user_id'] = user_info['id']
        session['username'] = user_info['username']
        session['real_name'] = user_info.get('real_name') or user_info.get('display_name', '')
        session['role'] = user_info['role']
        session['display_name'] = user_info.get('display_name', '')
        
        return success_response(data={
            'user_id': user_info['id'],
            'username': user_info['username'],
            'real_name': user_info.get('real_name') or user_info.get('display_name', ''),
            'role': user_info['role']
        }, message='登录成功')
    except Exception as e:
        log_exception(logger, "登录失败")
        return server_error_response(message=f'登录失败：{str(e)}')


@case_bp.route('/api/logout', methods=['POST'])
def logout():
    """登出"""
    session.clear()
    return success_response(message='登出成功')


@case_bp.route('/api/user/info', methods=['GET'])
def get_user_info():
    """获取用户信息"""
    user_id = session.get('user_id')
    if not user_id:
        return unauthorized_response(message='未登录')
    
    return success_response(data={
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'real_name': session.get('real_name'),
        'role': session.get('role'),
        'email': session.get('email')
    })


@case_bp.route('/api/ticket', methods=['POST'])
def create_ticket():
    """创建工单
    
    创建新的工单
    ---
    tags:
      - 工单-操作
    security:
      - CookieAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - customer_name
            - customer_contact
            - customer_email
            - product
            - issue_type
            - priority
            - title
            - content
          properties:
            customer_name:
              type: string
              description: 客户名称
            customer_contact:
              type: string
              description: 客户联系方式
            customer_email:
              type: string
              format: email
              description: 客户邮箱
            product:
              type: string
              description: 涉及产品
            issue_type:
              type: string
              enum: [technical, service, complaint, other]
              description: 问题类型
            priority:
              type: string
              enum: [low, medium, high, urgent]
              description: 优先级
            title:
              type: string
              description: 工单标题
            content:
              type: string
              description: 工单详情
    responses:
      200:
        description: 创建成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: 参数错误
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        log_request(logger, request, '/case/api/ticket')
        data = request.get_json()
        required_fields = [
            'customer_name', 'customer_contact', 'customer_email',
            'product', 'issue_type', 'priority', 'title', 'content'
        ]
        
        # 验证必填字段
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return error_response(message=f'缺少必填字段：{field}或字段值为空')
        
        customer_email = data['customer_email'].strip()
        is_valid, error_msg = validate_email(customer_email)
        if not is_valid:
            return error_response(message=error_msg)
        
        valid_issue_types = ['technical', 'service', 'complaint', 'other']
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if data['issue_type'].strip() not in valid_issue_types:
            return error_response(message='问题类型值不合法')
        if data['priority'].strip() not in valid_priorities:
            return error_response(message='优先级值不合法')
        
        ticket_id = generate_ticket_id()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with db_connection('case') as conn:
            cursor = conn.cursor()
            insert_sql = """
                INSERT INTO tickets (ticket_id, customer_name, customer_contact, customer_email,
                                    product, issue_type, priority, title, content,
                                    status, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (
                ticket_id, data['customer_name'].strip(), data['customer_contact'].strip(),
                customer_email, data['product'].strip(), data['issue_type'].strip(),
                data['priority'].strip(), data['title'].strip(), data['content'].strip(),
                'pending', now, now
            ))
            conn.commit()
        
        logger.info(f"工单创建成功: {ticket_id}")
        return success_response(data={'ticket_id': ticket_id}, message='工单创建成功')
    except Exception as e:
        log_exception(logger, "工单创建失败")
        return server_error_response(message=f'工单创建失败：{str(e)}')


@case_bp.route('/api/tickets', methods=['GET'])
def get_tickets():
    """获取工单列表"""
    try:
        log_request(logger, request, '/case/api/tickets')
        user_role = session.get('role')
        user_username = session.get('username')
        
        if not user_role:
            return unauthorized_response(message='未登录')
        
        status = request.args.get('status', '').strip()
        my_only = request.args.get('my_only', 'false').lower() == 'true'
        
        with db_connection('case') as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # customer 角色: 只能看到自己创建的工单
            if user_role == 'customer':
                if status:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE customer_name = %s AND status = %s ORDER BY create_time DESC
                    """
                    cursor.execute(select_sql, (user_username, status))
                else:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE customer_name = %s ORDER BY create_time DESC
                    """
                    cursor.execute(select_sql, (user_username,))
            # admin/user 角色: 可以查看所有工单，支持 my_only 筛选
            elif user_role in ['admin', 'user']:
                if status and my_only:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE status = %s ORDER BY create_time DESC LIMIT 100
                    """
                    cursor.execute(select_sql, (status,))
                elif status:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets WHERE status = %s ORDER BY create_time DESC LIMIT 100
                    """
                    cursor.execute(select_sql, (status,))
                else:
                    select_sql = """
                        SELECT ticket_id, customer_name, customer_contact, customer_email,
                               product, issue_type, priority, title, status, create_time
                        FROM tickets ORDER BY create_time DESC LIMIT 100
                    """
                    cursor.execute(select_sql)
            else:
                tickets = []
                return success_response(data=tickets, message='查询成功')
            
            tickets = cursor.fetchall()
        
        for ticket in tickets:
            ticket['create_time'] = ticket['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return success_response(data=tickets, message='查询成功')
    except Exception as e:
        log_exception(logger, "查询工单列表失败")
        return server_error_response(message=f'查询失败：{str(e)}')


@case_bp.route('/api/ticket/<ticket_id>', methods=['GET'])
def get_ticket_detail(ticket_id):
    """获取工单详情"""
    try:
        log_request(logger, request, f'/case/api/ticket/{ticket_id}')
        user_role = session.get('role')
        user_username = session.get('username')
        
        if not user_role:
            return unauthorized_response(message='未登录')
        
        with db_connection('case') as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            select_sql = "SELECT * FROM tickets WHERE ticket_id = %s"
            cursor.execute(select_sql, (ticket_id,))
            ticket = cursor.fetchone()
        
        if not ticket:
            from common.response import not_found_response
            return not_found_response(message='工单不存在')
        
        if user_role == 'customer' and ticket['customer_name'] != user_username:
            from common.response import forbidden_response
            return forbidden_response(message='无权访问此工单')
        
        ticket['create_time'] = ticket['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        ticket['update_time'] = ticket['update_time'].strftime('%Y-%m-%d %H:%M:%S')
        ticket['current_user_role'] = user_role
        
        return success_response(data=ticket, message='查询成功')
    except Exception as e:
        log_exception(logger, "查询工单详情失败")
        return server_error_response(message=f'查询失败：{str(e)}')


@case_bp.route('/api/ticket/<ticket_id>/status', methods=['PUT'])
def update_ticket_status(ticket_id):
    """更新工单状态"""
    try:
        log_request(logger, request, f'/case/api/ticket/{ticket_id}/status')
        user_role = session.get('role')
        if not user_role or user_role != 'admin':
            from common.response import forbidden_response
            return forbidden_response(message='无权执行此操作')
        
        data = request.get_json()
        new_status = data.get('status', '').strip()
        
        valid_statuses = ['pending', 'processing', 'completed', 'closed']
        if new_status not in valid_statuses:
            return error_response(message='工单状态值不合法')
        
        with db_connection('case') as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM tickets WHERE ticket_id = %s", (ticket_id,))
            if not cursor.fetchone():
                from common.response import not_found_response
                return not_found_response(message='工单不存在')
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_sql = "UPDATE tickets SET status = %s, update_time = %s WHERE ticket_id = %s"
            cursor.execute(update_sql, (new_status, now, ticket_id))
            conn.commit()
        
        logger.info(f"工单状态更新: {ticket_id} -> {new_status}")
        return success_response(message='工单状态更新成功')
    except Exception as e:
        log_exception(logger, "更新工单状态失败")
        return server_error_response(message=f'更新失败：{str(e)}')


@case_bp.route('/api/ticket/<ticket_id>/messages', methods=['GET'])
def get_messages(ticket_id):
    """获取工单消息"""
    try:
        log_request(logger, request, f'/case/api/ticket/{ticket_id}/messages')
        
        with db_connection('case') as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            select_sql = """
                SELECT id, ticket_id, sender, sender_name, content, send_time
                FROM messages WHERE ticket_id = %s ORDER BY send_time ASC
            """
            cursor.execute(select_sql, (ticket_id,))
            messages = cursor.fetchall()
        
        for msg in messages:
            msg['send_time'] = msg['send_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return success_response(data=messages, message='查询成功')
    except Exception as e:
        log_exception(logger, "查询工单消息失败")
        return server_error_response(message=f'查询失败：{str(e)}')
