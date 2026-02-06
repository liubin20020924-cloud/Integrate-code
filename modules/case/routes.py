"""
工单系统路由模块
"""
import re
import hashlib
import uuid
import pymysql
from datetime import datetime
from flask import Blueprint, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_socketio import emit, join_room, leave_room
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import os

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from common.db_manager import get_connection

# 创建蓝图
case_bp = Blueprint('case', __name__, url_prefix='/case')

# CORS配置
CORS(case_bp, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                                "allow_headers": ["Content-Type", "Authorization"]}},
     supports_credentials=True)


def get_db_connection():
    """获取工单系统数据库连接"""
    return get_connection('case')


def is_valid_email(email):
    """校验邮箱格式是否合法"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None


def generate_ticket_id():
    """生成唯一工单ID"""
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = str(uuid.uuid4())[:6].upper()
    return f"TK-{now}-{random_str}"


# ==================== 认证相关接口 ====================
@case_bp.route('/api/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'code': 400, 'msg': '用户名和密码不能为空'}), 400

        password_hash = hashlib.md5(password.encode()).hexdigest()

        cursor = get_db_cursor()
        if not cursor:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500

        select_sql = "SELECT id, username, password, real_name, role, email FROM users WHERE username = %s"
        cursor.execute(select_sql, (username,))
        user = cursor.fetchone()
        cursor.close()
        get_db_connection().close()

        if not user:
            return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

        if user['password'] != password_hash:
            return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['real_name'] = user['real_name']
        session['role'] = user['role']
        session['email'] = user['email']

        return jsonify({
            'code': 200,
            'msg': '登录成功',
            'data': {
                'user_id': user['id'],
                'username': user['username'],
                'real_name': user['real_name'],
                'role': user['role'],
                'email': user['email']
            }
        })
    except Exception as e:
        print(f"登录异常：{e}")
        return jsonify({'code': 500, 'msg': f'登录失败：{str(e)}'}), 500


@case_bp.route('/api/register', methods=['POST'])
def register():
    """客户注册接口"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()

        required_fields = ['username', 'password', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'code': 400, 'msg': f'缺少必填字段：{field}'}), 400

        if not is_valid_email(email):
            return jsonify({'code': 400, 'msg': '邮箱格式不合法'}), 400

        if len(password) < 6:
            return jsonify({'code': 400, 'msg': '密码长度不能少于6位'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'code': 400, 'msg': '用户名已存在'}), 400

        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'code': 400, 'msg': '邮箱已被注册'}), 400

        password_hash = hashlib.md5(password.encode()).hexdigest()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        insert_sql = "INSERT INTO users (username, password, real_name, role, email, create_time) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_sql, (username, password_hash, username, 'customer', email, now))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'code': 200, 'msg': '注册成功，请登录'})
    except Exception as e:
        print(f"注册异常：{e}")
        return jsonify({'code': 500, 'msg': f'注册失败：{str(e)}'}), 500


@case_bp.route('/api/logout', methods=['POST'])
def logout():
    """用户登出接口"""
    session.clear()
    return jsonify({'code': 200, 'msg': '登出成功'})


@case_bp.route('/api/user/info', methods=['GET'])
def get_user_info():
    """获取当前登录用户信息"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'msg': '未登录'}), 401

    return jsonify({
        'code': 200,
        'msg': '获取成功',
        'data': {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'real_name': session.get('real_name'),
            'role': session.get('role'),
            'email': session.get('email')
        }
    })


# ==================== 工单相关接口 ====================
@case_bp.route('/api/ticket', methods=['POST'])
def create_ticket():
    """创建工单接口"""
    try:
        data = request.get_json()
        required_fields = [
            'customer_name', 'customer_contact', 'customer_email',
            'product', 'issue_type', 'priority', 'title', 'content'
        ]

        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({'code': 400, 'msg': f'缺少必填字段：{field}或字段值为空'}), 400

        customer_name = data['customer_name'].strip()
        customer_contact = data['customer_contact'].strip()
        customer_email = data['customer_email'].strip()
        product = data['product'].strip()
        issue_type = data['issue_type'].strip()
        priority = data['priority'].strip()
        title = data['title'].strip()
        content = data['content'].strip()

        if not is_valid_email(customer_email):
            return jsonify({'code': 400, 'msg': '客户邮箱格式不合法'}), 400

        valid_issue_types = ['technical', 'service', 'complaint', 'other']
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if issue_type not in valid_issue_types:
            return jsonify({'code': 400, 'msg': '问题类型值不合法'}), 400
        if priority not in valid_priorities:
            return jsonify({'code': 400, 'msg': '优先级值不合法'}), 400

        ticket_id = generate_ticket_id()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
        cursor = conn.cursor()
        insert_sql = """
            INSERT INTO tickets (ticket_id, customer_name, customer_contact, customer_email,
                                product, issue_type, priority, title, content,
                                status, create_time, update_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        insert_data = (
            ticket_id, customer_name, customer_contact, customer_email,
            product, issue_type, priority, title, content,
            'pending', now, now
        )
        cursor.execute(insert_sql, insert_data)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'code': 200,
            'msg': '工单创建成功',
            'data': {'ticket_id': ticket_id}
        })
    except Exception as e:
        print(f"创建工单异常：{e}")
        return jsonify({'code': 500, 'msg': f'工单创建失败：{str(e)}'}), 500


@case_bp.route('/api/tickets', methods=['GET'])
def get_tickets():
    """查询工单列表接口"""
    try:
        user_role = session.get('role')
        user_username = session.get('username')

        if not user_role:
            return jsonify({'code': 401, 'msg': '未登录'}), 401

        status = request.args.get('status', '').strip()
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        if user_role == 'customer' and user_username:
            if status:
                select_sql = """
                    SELECT ticket_id, customer_name, customer_contact, customer_email,
                           product, issue_type, priority, title, status, create_time
                    FROM tickets
                    WHERE customer_name = %s AND status = %s
                    ORDER BY create_time DESC
                """
                cursor.execute(select_sql, (user_username, status))
            else:
                select_sql = """
                    SELECT ticket_id, customer_name, customer_contact, customer_email,
                           product, issue_type, priority, title, status, create_time
                    FROM tickets
                    WHERE customer_name = %s
                    ORDER BY create_time DESC
                """
                cursor.execute(select_sql, (user_username,))
        elif user_role == 'admin':
            if status:
                select_sql = """
                    SELECT ticket_id, customer_name, customer_contact, customer_email,
                           product, issue_type, priority, title, status, create_time
                    FROM tickets
                    WHERE status = %s
                    ORDER BY create_time DESC
                """
                cursor.execute(select_sql, (status,))
            else:
                select_sql = """
                    SELECT ticket_id, customer_name, customer_contact, customer_email,
                           product, issue_type, priority, title, status, create_time
                    FROM tickets
                    ORDER BY create_time DESC
                """
                cursor.execute(select_sql)
        else:
            tickets = []
            cursor.close()
            conn.close()
            return jsonify({'code': 200, 'msg': '查询成功', 'data': tickets})

        tickets = cursor.fetchall()
        cursor.close()
        conn.close()

        for ticket in tickets:
            ticket['create_time'] = ticket['create_time'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({'code': 200, 'msg': '查询成功', 'data': tickets})
    except Exception as e:
        print(f"查询工单列表异常：{e}")
        return jsonify({'code': 500, 'msg': f'查询失败：{str(e)}'}), 500


@case_bp.route('/api/ticket/<ticket_id>', methods=['GET'])
def get_ticket_detail(ticket_id):
    """查询工单详情接口"""
    try:
        user_role = session.get('role')
        user_username = session.get('username')

        if not user_role:
            return jsonify({'code': 401, 'msg': '未登录'}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        select_sql = "SELECT * FROM tickets WHERE ticket_id = %s"
        cursor.execute(select_sql, (ticket_id,))
        ticket = cursor.fetchone()
        cursor.close()
        conn.close()

        if not ticket:
            return jsonify({'code': 404, 'msg': '工单不存在'}), 404

        if user_role == 'customer' and ticket['customer_name'] != user_username:
            return jsonify({'code': 403, 'msg': '无权访问此工单'}), 403

        ticket['create_time'] = ticket['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        ticket['update_time'] = ticket['update_time'].strftime('%Y-%m-%d %H:%M:%S')
        ticket['current_user_role'] = user_role

        return jsonify({'code': 200, 'msg': '查询成功', 'data': ticket})
    except Exception as e:
        print(f"查询工单详情异常：{e}")
        return jsonify({'code': 500, 'msg': f'查询失败：{str(e)}'}), 500


@case_bp.route('/api/ticket/<ticket_id>/status', methods=['PUT'])
def update_ticket_status(ticket_id):
    """更新工单状态接口"""
    try:
        user_role = session.get('role')
        if not user_role or user_role != 'admin':
            return jsonify({'code': 403, 'msg': '无权执行此操作'}), 403

        data = request.get_json()
        new_status = data.get('status', '').strip()

        valid_statuses = ['pending', 'processing', 'completed', 'closed']
        if new_status not in valid_statuses:
            return jsonify({'code': 400, 'msg': '工单状态值不合法'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tickets WHERE ticket_id = %s", (ticket_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'code': 404, 'msg': '工单不存在'}), 404

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_sql = "UPDATE tickets SET status = %s, update_time = %s WHERE ticket_id = %s"
        cursor.execute(update_sql, (new_status, now, ticket_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'code': 200, 'msg': '工单状态更新成功'})
    except Exception as e:
        print(f"更新工单状态异常：{e}")
        return jsonify({'code': 500, 'msg': f'更新失败：{str(e)}'}), 500


@case_bp.route('/api/ticket/<ticket_id>/messages', methods=['GET'])
def get_messages(ticket_id):
    """获取工单的所有历史消息"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        select_sql = """
            SELECT id, ticket_id, sender, sender_name, content, send_time
            FROM messages
            WHERE ticket_id = %s
            ORDER BY send_time ASC
        """
        cursor.execute(select_sql, (ticket_id,))
        messages = cursor.fetchall()
        cursor.close()
        conn.close()

        for msg in messages:
            msg['send_time'] = msg['send_time'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({'code': 200, 'msg': '查询成功', 'data': messages})
    except Exception as e:
        print(f"查询消息异常：{e}")
        return jsonify({'code': 500, 'msg': f'查询失败：{str(e)}'}), 500


@case_bp.route('/api/send-email', methods=['POST'])
def send_email():
    """发送邮件接口"""
    try:
        user_role = session.get('role')
        if not user_role or user_role != 'admin':
            return jsonify({'code': 403, 'msg': '无权执行此操作'}), 403

        data = request.get_json()
        to_email = data.get('to', '').strip()
        subject = data.get('subject', '').strip()
        content = data.get('content', '').strip()

        if not to_email or not subject or not content:
            return jsonify({'code': 400, 'msg': '缺少邮件必填参数（接收人/标题/内容）'}), 400
        if not is_valid_email(to_email):
            return jsonify({'code': 400, 'msg': '接收邮箱格式不合法'}), 400

        msg = MIMEText(content, 'html', 'utf-8')
        msg['From'] = formataddr(['工单系统', config.EMAIL_SENDER])
        msg['To'] = to_email
        msg['Subject'] = subject

        with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.sendmail(config.EMAIL_SENDER, to_email, msg.as_string())

        return jsonify({'code': 200, 'msg': '邮件发送成功'})
    except smtplib.SMTPException as e:
        print(f"邮件发送SMTP异常：{e}")
        return jsonify({'code': 500, 'msg': f'邮件发送失败：SMTP错误-{str(e)}'}), 500
    except Exception as e:
        print(f"邮件发送全局异常：{e}")
        return jsonify({'code': 500, 'msg': f'邮件发送失败：{str(e)}'}), 500


# ==================== 静态文件服务 ====================
@case_bp.route('/')
def index():
    """首页重定向到登录页"""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'case')
    return send_from_directory(frontend_dir, 'login.html')


@case_bp.route('/<path:filename>')
def serve_frontend(filename):
    """提供前端静态文件"""
    try:
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'case')
        return send_from_directory(frontend_dir, filename)
    except:
        return "404 - 文件未找到", 404


# ==================== WebSocket事件处理 ====================
def register_socketio_events(socketio):
    """注册SocketIO事件"""

    @socketio.on('connect')
    def handle_connect():
        print(f'客户端已连接：{request.sid}')

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'客户端已断开连接：{request.sid}')

    @socketio.on('join_ticket')
    def handle_join_ticket(data):
        ticket_id = data.get('ticket_id')
        user_type = data.get('user_type')
        user_name = data.get('user_name', '匿名用户')

        if ticket_id:
            room = f'ticket_{ticket_id}'
            join_room(room)
            print(f'{user_name} ({user_type}) 加入了工单 {ticket_id} 聊天室')

            emit('notification', {
                'message': f'{user_name} 加入了聊天',
                'user_type': user_type
            }, room=room, skip_sid=request.sid)

    @socketio.on('leave_ticket')
    def handle_leave_ticket(data):
        ticket_id = data.get('ticket_id')
        user_type = data.get('user_type')
        user_name = data.get('user_name', '匿名用户')

        if ticket_id:
            room = f'ticket_{ticket_id}'
            leave_room(room)
            print(f'{user_name} ({user_type}) 离开了工单 {ticket_id} 聊天室')

            emit('notification', {
                'message': f'{user_name} 离开了聊天',
                'user_type': user_type
            }, room=room, skip_sid=request.sid)

    @socketio.on('send_message')
    def handle_send_message(data):
        ticket_id = data.get('ticket_id')
        sender = data.get('sender')
        sender_name = data.get('sender_name')
        content = data.get('content')

        if not all([ticket_id, sender, sender_name, content]):
            return {'success': False, 'message': '消息参数不完整'}

        try:
            conn = get_db_connection()
            if not conn:
                return {'success': False, 'message': '数据库连接失败'}
            cursor = conn.cursor()

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            insert_sql = """
                INSERT INTO messages (ticket_id, sender, sender_name, content, send_time)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (ticket_id, sender, sender_name, content, now))
            conn.commit()

            message_id = cursor.lastrowid
            cursor.close()
            conn.close()

            message_data = {
                'id': message_id,
                'ticket_id': ticket_id,
                'sender': sender,
                'sender_name': sender_name,
                'content': content,
                'send_time': now
            }

            room = f'ticket_{ticket_id}'
            emit('new_message', message_data, room=room)

            return {'success': True, 'message': '消息发送成功'}
        except Exception as e:
            print(f"发送消息异常：{e}")
            return {'success': False, 'message': f'发送失败：{str(e)}'}


# ==================== 数据库初始化 ====================
def init_database():
    """初始化工单系统数据库表"""
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()

    # 创建工单表
    create_ticket_sql = """
        CREATE TABLE IF NOT EXISTS tickets (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增ID',
            ticket_id VARCHAR(32) NOT NULL UNIQUE COMMENT '工单唯一标识ID',
            customer_name VARCHAR(100) NOT NULL COMMENT '客户名称',
            customer_contact VARCHAR(50) NOT NULL COMMENT '客户联系方式',
            customer_email VARCHAR(100) NOT NULL COMMENT '客户邮箱',
            product VARCHAR(50) NOT NULL COMMENT '涉及产品',
            issue_type VARCHAR(20) NOT NULL COMMENT '问题类型',
            priority VARCHAR(10) NOT NULL COMMENT '工单优先级',
            title VARCHAR(200) NOT NULL COMMENT '问题标题',
            content TEXT NOT NULL COMMENT '问题详情',
            status VARCHAR(10) DEFAULT 'pending' COMMENT '工单状态',
            create_time DATETIME NOT NULL COMMENT '创建时间',
            update_time DATETIME NOT NULL COMMENT '更新时间',
            INDEX idx_ticket_id (ticket_id),
            INDEX idx_customer_name (customer_name),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单系统主表'
    """

    # 创建消息表
    create_message_sql = """
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '消息ID',
            ticket_id VARCHAR(32) NOT NULL COMMENT '工单ID',
            sender VARCHAR(20) NOT NULL COMMENT '发送者',
            sender_name VARCHAR(100) NOT NULL COMMENT '发送者名称',
            content TEXT NOT NULL COMMENT '消息内容',
            send_time DATETIME NOT NULL COMMENT '发送时间',
            INDEX idx_ticket_id (ticket_id),
            INDEX idx_send_time (send_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单聊天消息表'
    """

    # 创建用户表
    create_user_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
            username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
            password VARCHAR(64) NOT NULL COMMENT '密码（MD5加密）',
            real_name VARCHAR(100) NOT NULL COMMENT '真实姓名',
            role VARCHAR(20) NOT NULL COMMENT '角色',
            email VARCHAR(100) COMMENT '邮箱',
            create_time DATETIME NOT NULL COMMENT '创建时间',
            INDEX idx_username (username)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表'
    """

    try:
        cursor.execute(create_ticket_sql)
        cursor.execute(create_message_sql)
        cursor.execute(create_user_sql)
        conn.commit()

        # 创建默认管理员
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            admin_password = hashlib.md5('admin123'.encode()).hexdigest()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "INSERT INTO users (username, password, real_name, role, email, create_time) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                ('admin', admin_password, '系统管理员', 'admin', '1919516011@qq.com', now)
            )
            conn.commit()
            print("工单系统默认管理员已创建：用户名 admin，密码 admin123")

        print("工单系统数据库表初始化成功")
    except pymysql.MySQLError as e:
        conn.rollback()
        print(f"工单系统数据库初始化失败：{e}")
    finally:
        cursor.close()
        conn.close()
