# 导入所需模块
from flask import Flask, request, jsonify, session, send_from_directory
import smtplib
import pymysql
import uuid
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import re
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS  # 新增导入
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
from functools import wraps
from dbutils.pooled_db import PooledDB

# 初始化Flask应用
app = Flask(__name__)
# 关键配置：允许所有域名跨域请求，支持带凭证，返回所有需要的响应头
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}}, supports_credentials=True)
app.config['JSON_AS_ASCII'] = False  # 解决中文乱码
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'  # Session密钥
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # 允许跨域Cookie
app.config['SESSION_COOKIE_HTTPONLY'] = True

# 设置静态文件目录
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# -------------------------- 配置区（请根据自己的实际信息修改！！！）--------------------------
# 1. 数据库连接配置（MySQL/MariaDB）
DB_CONFIG = {
    'host': '127.0.0.1',  # 数据库地址，本地填127.0.0.1
    'port': 3306,  # 数据库端口，默认3306
    'user': 'root',  # 数据库用户名
    'password': 'nutanix/4u',  # 数据库密码（自己的MySQL密码）
    'database': 'casedb',  # 数据库名（需提前创建，如ticket_sys）
    'charset': 'utf8mb4'  # 字符集，支持中文/emoji
}

# 2. 发件邮箱SMTP配置（之前配置过，直接复制过来即可）
EMAIL_CONFIG = {
    'smtp_server': 'smtp.qq.com',  # 发件邮箱SMTP服务器（163:smtp.163.com | QQ:smtp.qq.com）
    'smtp_port': 465,  # SSL端口，固定465
    'smtp_username': '1919516011@qq.com',  # 发件邮箱完整地址
    'smtp_password': 'xrbvyjjfkpdmcfbj',  # 发件邮箱授权码（不是登录密码！）
    'sender': '1919516011@qq.com'  # 发件人，和上面一致
}


# -------------------------------------------------------------------------------------------

# 初始化数据库连接池
db_pool = PooledDB(
    creator=pymysql,
    maxconnections=20,  # 最大连接数
    mincached=5,  # 初始化时创建的空闲连接数
    maxcached=10,  # 最大空闲连接数
    maxshared=5,  # 最大共享连接数
    blocking=True,  # 连接池满时是否阻塞等待
    ping=1,  # ping MySQL服务端，检查是否可用
    **DB_CONFIG
)

def get_db_connection():
    """从连接池获取数据库连接"""
    try:
        return db_pool.connection()
    except Exception as e:
        print(f"数据库连接失败：{e}")
        return None


# 数据库连接上下文管理器（连接池版本）
def with_db_connection(func):
    """数据库连接装饰器，自动管理连接的打开和归还到连接池"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
            result = func(conn, *args, **kwargs)
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"数据库操作异常：{e}")
            return jsonify({'code': 500, 'msg': f'操作失败：{str(e)}'}), 500
        finally:
            if conn:
                conn.close()  # 连接池会自动管理连接，这里只是归还连接
    return wrapper


# 初始化工单表（首次运行自动创建，包含新增字段）
def init_ticket_table():
    """创建工单表（若不存在），包含客户名称/邮箱/产品/优先级等新字段"""
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    # 工单表SQL：新增customer_name/customer_email/product/priority字段
    create_sql = """
                 CREATE TABLE IF NOT EXISTS tickets \
                 ( \
                     id \
                     INT \
                     AUTO_INCREMENT \
                     PRIMARY \
                     KEY \
                     COMMENT \
                     '自增ID', \
                     ticket_id \
                     VARCHAR \
                 ( \
                     32 \
                 ) NOT NULL UNIQUE COMMENT '工单唯一标识ID',
                     customer_name VARCHAR \
                 ( \
                     100 \
                 ) NOT NULL COMMENT '客户名称',
                     customer_contact VARCHAR \
                 ( \
                     50 \
                 ) NOT NULL COMMENT '客户联系方式',
                     customer_email VARCHAR \
                 ( \
                     100 \
                 ) NOT NULL COMMENT '客户邮箱',
                     product VARCHAR \
                 ( \
                     50 \
                 ) NOT NULL COMMENT '涉及产品',
                     issue_type VARCHAR \
                 ( \
                     20 \
                 ) NOT NULL COMMENT '问题类型',
                     priority VARCHAR \
                 ( \
                     10 \
                 ) NOT NULL COMMENT '工单优先级',
                     title VARCHAR \
                 ( \
                     200 \
                 ) NOT NULL COMMENT '问题标题',
                     content TEXT NOT NULL COMMENT '问题详情',
                     status VARCHAR \
                 ( \
                     10 \
                 ) DEFAULT 'pending' COMMENT '工单状态（pending/processing/completed/closed）',
                     create_time DATETIME NOT NULL COMMENT '创建时间',
                     update_time DATETIME NOT NULL COMMENT '更新时间',
                     INDEX idx_ticket_id \
                 ( \
                     ticket_id \
                 ),
                     INDEX idx_customer_name \
                 ( \
                     customer_name \
                 ),
                     INDEX idx_status \
                 ( \
                     status \
                 )
                     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单系统主表'; \
                 """
    try:
        cursor.execute(create_sql)
        conn.commit()
        print("工单表初始化成功（含新字段）")
    except pymysql.MySQLError as e:
        conn.rollback()
        print(f"工单表创建失败：{e}")
    finally:
        cursor.close()
        conn.close()


# 初始化消息表
def init_message_table():
    """创建消息表，用于存储客服与客户的实时聊天记录"""
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    create_sql = """
                 CREATE TABLE IF NOT EXISTS messages \
                 ( \
                     id INT AUTO_INCREMENT PRIMARY KEY COMMENT '消息ID', \
                     ticket_id VARCHAR(32) NOT NULL COMMENT '工单ID', \
                     sender VARCHAR(20) NOT NULL COMMENT '发送者（customer/service）', \
                     sender_name VARCHAR(100) NOT NULL COMMENT '发送者名称', \
                     content TEXT NOT NULL COMMENT '消息内容', \
                     send_time DATETIME NOT NULL COMMENT '发送时间', \
                     INDEX idx_ticket_id (ticket_id), \
                     INDEX idx_send_time (send_time) \
                 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单聊天消息表'; \
                 """
    try:
        cursor.execute(create_sql)
        conn.commit()
        print("消息表初始化成功")
    except pymysql.MySQLError as e:
        conn.rollback()
        print(f"消息表创建失败：{e}")
    finally:
        cursor.close()
        conn.close()


# 初始化用户表
def init_user_table():
    """创建用户表，用于存储客户和管理员信息"""
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    create_sql = """
                 CREATE TABLE IF NOT EXISTS users \
                 ( \
                     id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID', \
                     username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名', \
                     password VARCHAR(64) NOT NULL COMMENT '密码（MD5加密）', \
                     real_name VARCHAR(100) NOT NULL COMMENT '真实姓名', \
                     role VARCHAR(20) NOT NULL COMMENT '角色（customer/admin）', \
                     email VARCHAR(100) COMMENT '邮箱', \
                     create_time DATETIME NOT NULL COMMENT '创建时间', \
                     INDEX idx_username (username) \
                 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表'; \
                 """
    try:
        cursor.execute(create_sql)
        conn.commit()

        # 检查是否存在默认管理员，不存在则创建
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
            print("默认管理员已创建：用户名 admin，密码 admin123")

        print("用户表初始化成功")
    except pymysql.MySQLError as e:
        conn.rollback()
        print(f"用户表创建失败：{e}")
    finally:
        cursor.close()
        conn.close()


# 邮箱格式校验工具函数
def is_valid_email(email):
    """校验邮箱格式是否合法"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None


# 生成唯一工单ID
def generate_ticket_id():
    """生成唯一工单ID（时间戳+随机字符，便于识别）"""
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = str(uuid.uuid4())[:6].upper()
    return f"TK-{now}-{random_str}"


# -------------------------- 接口区（适配前端新功能）--------------------------
# -------------------------- 认证相关接口 --------------------------
@app.route('/api/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'code': 400, 'msg': '用户名和密码不能为空'}), 400

        # MD5加密密码
        password_hash = hashlib.md5(password.encode()).hexdigest()

        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        select_sql = """
                     SELECT id, username, password, real_name, role, email \
                     FROM users \
                     WHERE username = %s \
                     """
        cursor.execute(select_sql, (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

        if user['password'] != password_hash:
            return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

        # 存储用户信息到session（注意：实际生产环境应使用JWT）
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


@app.route('/api/register', methods=['POST'])
def register():
    """客户注册接口"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()

        # 校验必填字段
        required_fields = ['username', 'password', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'code': 400, 'msg': f'缺少必填字段：{field}'}), 400

        # 校验邮箱格式
        if not is_valid_email(email):
            return jsonify({'code': 400, 'msg': '邮箱格式不合法'}), 400

        # 校验密码长度
        if len(password) < 6:
            return jsonify({'code': 400, 'msg': '密码长度不能少于6位'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
        cursor = conn.cursor()

        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'code': 400, 'msg': '用户名已存在'}), 400

        # 检查邮箱是否已存在
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'code': 400, 'msg': '邮箱已被注册'}), 400

        # 创建客户账号 - 使用用户名作为真实姓名
        password_hash = hashlib.md5(password.encode()).hexdigest()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        insert_sql = """
                     INSERT INTO users (username, password, real_name, role, email, create_time) \
                     VALUES (%s, %s, %s, %s, %s, %s) \
                     """
        cursor.execute(insert_sql, (username, password_hash, username, 'customer', email, now))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'code': 200, 'msg': '注册成功，请登录'})
    except Exception as e:
        print(f"注册异常：{e}")
        return jsonify({'code': 500, 'msg': f'注册失败：{str(e)}'}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    """用户登出接口"""
    session.clear()
    return jsonify({'code': 200, 'msg': '登出成功'})


@app.route('/api/user/info', methods=['GET'])
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


# -------------------------- 接口区（适配前端新功能）--------------------------
@app.route('/api/ticket', methods=['POST'])
def create_ticket():
    """创建工单接口 - 适配前端新字段：客户名称/邮箱/产品/优先级"""
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()
        # 提取核心字段（含前端新传的扩展字段）
        required_fields = [
            'customer_name', 'customer_contact', 'customer_email',
            'product', 'issue_type', 'priority', 'title', 'content'
        ]
        # 校验必填字段是否齐全
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({'code': 400, 'msg': f'缺少必填字段：{field}或字段值为空'}), 400

        # 提取并清洗字段值（去除首尾空格）
        customer_name = data['customer_name'].strip()
        customer_contact = data['customer_contact'].strip()
        customer_email = data['customer_email'].strip()
        product = data['product'].strip()
        issue_type = data['issue_type'].strip()
        priority = data['priority'].strip()
        title = data['title'].strip()
        content = data['content'].strip()

        # 校验邮箱格式是否合法
        if not is_valid_email(customer_email):
            return jsonify({'code': 400, 'msg': '客户邮箱格式不合法，请填写正确的邮箱地址'}), 400

        # 校验产品/优先级/问题类型是否为合法值（可选，前端已做下拉限制，后端做二次校验）
        valid_issue_types = ['technical', 'service', 'complaint', 'other']
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if issue_type not in valid_issue_types:
            return jsonify({'code': 400, 'msg': '问题类型值不合法'}), 400
        if priority not in valid_priorities:
            return jsonify({'code': 400, 'msg': '优先级值不合法'}), 400

        # 生成唯一工单ID
        ticket_id = generate_ticket_id()
        # 获取当前时间（MySQL DATETIME格式）
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 插入数据库（包含所有新字段）
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败，无法创建工单'}), 500
        cursor = conn.cursor()
        insert_sql = """
                     INSERT INTO tickets (ticket_id, customer_name, customer_contact, customer_email, \
                                          product, issue_type, priority, title, content, \
                                          status, create_time, update_time) \
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
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

        # 返回成功结果，传递工单ID给前端
        return jsonify({
            'code': 200,
            'msg': '工单创建成功',
            'data': {'ticket_id': ticket_id}
        })
    except Exception as e:
        # 全局异常捕获
        print(f"创建工单异常：{e}")
        return jsonify({'code': 500, 'msg': f'工单创建失败：{str(e)}'}), 500


@app.route('/api/send-email', methods=['POST'])
def send_email():
    """发送邮件接口 - 逻辑通用，无需修改！适配前端双邮箱发送"""
    try:
        # 权限检查：只有管理员可以发送邮件
        user_role = session.get('role')
        if not user_role or user_role != 'admin':
            return jsonify({'code': 403, 'msg': '无权执行此操作'}), 403

        # 获取前端传递的邮件参数（to:接收人, subject:标题, content:内容）
        data = request.get_json()
        to_email = data.get('to', '').strip()
        subject = data.get('subject', '').strip()
        content = data.get('content', '').strip()

        # 校验邮件参数
        if not to_email or not subject or not content:
            return jsonify({'code': 400, 'msg': '缺少邮件必填参数（接收人/标题/内容）'}), 400
        if not is_valid_email(to_email):
            return jsonify({'code': 400, 'msg': '接收邮箱格式不合法'}), 400

        # 构造HTML邮件内容（支持前端传递的HTML格式）
        msg = MIMEText(content, 'html', 'utf-8')
        # From头使用formataddr方法，符合RFC5322标准
        msg['From'] = formataddr(['工单系统', EMAIL_CONFIG['sender']])
        msg['To'] = to_email
        msg['Subject'] = subject

        # 发送邮件（SSL加密）
        with smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
            server.sendmail(EMAIL_CONFIG['sender'], to_email, msg.as_string())

        return jsonify({'code': 200, 'msg': '邮件发送成功'})
    except smtplib.SMTPException as e:
        print(f"邮件发送SMTP异常：{e}")
        return jsonify({'code': 500, 'msg': f'邮件发送失败：SMTP错误-{str(e)}'}), 500
    except Exception as e:
        print(f"邮件发送全局异常：{e}")
        return jsonify({'code': 500, 'msg': f'邮件发送失败：{str(e)}'}), 500


@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    """查询工单列表接口 - 适配新字段，返回完整工单信息"""
    try:
        # 获取当前登录用户信息
        user_role = session.get('role')
        user_username = session.get('username')  # 获取用户名

        # 权限检查：未登录用户无法访问
        if not user_role:
            return jsonify({'code': 401, 'msg': '未登录'}), 401

        # 可选：按状态筛选（前端传递status参数，如?status=pending）
        status = request.args.get('status', '').strip()
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
        cursor = conn.cursor(pymysql.cursors.DictCursor)  # 返回字典格式，便于前端处理
        # 构造查询SQL
        if user_role == 'customer' and user_username:
            # 客户只能查看自己的工单（按客户名称与用户名匹配）
            if status:
                select_sql = """
                             SELECT ticket_id, \
                                    customer_name, \
                                    customer_contact, \
                                    customer_email,
                                    product, \
                                    issue_type, \
                                    priority, \
                                    title, \
                                    status, \
                                    create_time
                             FROM tickets \
                             WHERE customer_name = %s AND status = %s \
                             ORDER BY create_time DESC \
                             """
                cursor.execute(select_sql, (user_username, status))
            else:
                select_sql = """
                             SELECT ticket_id, \
                                    customer_name, \
                                    customer_contact, \
                                    customer_email,
                                    product, \
                                    issue_type, \
                                    priority, \
                                    title, \
                                    status, \
                                    create_time
                             FROM tickets \
                             WHERE customer_name = %s \
                             ORDER BY create_time DESC \
                             """
                cursor.execute(select_sql, (user_username,))
        elif user_role == 'admin':
            # 管理员可以查看所有工单
            if status:
                select_sql = """
                             SELECT ticket_id, \
                                    customer_name, \
                                    customer_contact, \
                                    customer_email,
                                    product, \
                                    issue_type, \
                                    priority, \
                                    title, \
                                    status, \
                                    create_time
                             FROM tickets \
                             WHERE status = %s \
                             ORDER BY create_time DESC \
                             """
                cursor.execute(select_sql, (status,))
            else:
                select_sql = """
                             SELECT ticket_id, \
                                    customer_name, \
                                    customer_contact, \
                                    customer_email,
                                    product, \
                                    issue_type, \
                                    priority, \
                                    title, \
                                    status, \
                                    create_time
                             FROM tickets \
                             ORDER BY create_time DESC \
                             """
                cursor.execute(select_sql)
        else:
            # 其他情况返回空列表
            tickets = []
            cursor.close()
            conn.close()
            return jsonify({
                'code': 200,
                'msg': '查询成功',
                'data': tickets
            })
        tickets = cursor.fetchall()
        cursor.close()
        conn.close()

        # 时间格式化（便于前端显示）
        for ticket in tickets:
            ticket['create_time'] = ticket['create_time'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'code': 200,
            'msg': '查询成功',
            'data': tickets
        })
    except Exception as e:
        print(f"查询工单列表异常：{e}")
        return jsonify({'code': 500, 'msg': f'查询失败：{str(e)}'}), 500


@app.route('/api/ticket/<ticket_id>', methods=['GET'])
def get_ticket_detail(ticket_id):
    """查询工单详情接口 - 适配新字段，返回完整信息"""
    try:
        # 获取当前登录用户信息
        user_role = session.get('role')
        user_username = session.get('username')  # 获取用户名

        # 权限检查
        if not user_role:
            return jsonify({'code': 401, 'msg': '未登录'}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        select_sql = """
                     SELECT * \
                     FROM tickets \
                     WHERE ticket_id = %s \
                     """
        cursor.execute(select_sql, (ticket_id,))
        ticket = cursor.fetchone()
        cursor.close()
        conn.close()

        if not ticket:
            return jsonify({'code': 404, 'msg': '工单不存在'}), 404

        # 权限检查：客户只能查看自己的工单（客户名称与用户名匹配）
        if user_role == 'customer' and ticket['customer_name'] != user_username:
            return jsonify({'code': 403, 'msg': '无权访问此工单'}), 403

        # 时间格式化
        ticket['create_time'] = ticket['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        ticket['update_time'] = ticket['update_time'].strftime('%Y-%m-%d %H:%M:%S')

        # 添加用户权限信息到响应中
        ticket['current_user_role'] = user_role

        return jsonify({
            'code': 200,
            'msg': '查询成功',
            'data': ticket
        })
    except Exception as e:
        print(f"查询工单详情异常：{e}")
        return jsonify({'code': 500, 'msg': f'查询失败：{str(e)}'}), 500


@app.route('/api/ticket/<ticket_id>/status', methods=['PUT'])
def update_ticket_status(ticket_id):
    """更新工单状态接口"""
    try:
        # 权限检查：只有管理员可以更新工单状态
        user_role = session.get('role')
        if not user_role or user_role != 'admin':
            return jsonify({'code': 403, 'msg': '无权执行此操作'}), 403

        # 获取前端传递的JSON数据
        data = request.get_json()
        new_status = data.get('status', '').strip()

        # 校验状态值是否合法
        valid_statuses = ['pending', 'processing', 'completed', 'closed']
        if new_status not in valid_statuses:
            return jsonify({'code': 400, 'msg': '工单状态值不合法'}), 400

        # 连接数据库并更新
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
        cursor = conn.cursor()

        # 检查工单是否存在
        cursor.execute("SELECT id FROM tickets WHERE ticket_id = %s", (ticket_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'code': 404, 'msg': '工单不存在'}), 404

        # 更新状态和时间
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_sql = """
                     UPDATE tickets \
                     SET status = %s, update_time = %s \
                     WHERE ticket_id = %s \
                     """
        cursor.execute(update_sql, (new_status, now, ticket_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'code': 200,
            'msg': '工单状态更新成功'
        })
    except Exception as e:
        print(f"更新工单状态异常：{e}")
        return jsonify({'code': 500, 'msg': f'更新失败：{str(e)}'}), 500


# -------------------------- 消息接口 --------------------------
@app.route('/api/ticket/<ticket_id>/messages', methods=['GET'])
def get_messages(ticket_id):
    """获取工单的所有历史消息"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'msg': '数据库连接失败'}), 500
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        select_sql = """
                     SELECT id, ticket_id, sender, sender_name, content, send_time \
                     FROM messages \
                     WHERE ticket_id = %s \
                     ORDER BY send_time ASC \
                     """
        cursor.execute(select_sql, (ticket_id,))
        messages = cursor.fetchall()
        cursor.close()
        conn.close()

        # 时间格式化
        for msg in messages:
            msg['send_time'] = msg['send_time'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'code': 200,
            'msg': '查询成功',
            'data': messages
        })
    except Exception as e:
        print(f"查询消息异常：{e}")
        return jsonify({'code': 500, 'msg': f'查询失败：{str(e)}'}), 500


# -------------------------- WebSocket事件处理 --------------------------
@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print(f'客户端已连接：{request.sid}')


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    print(f'客户端已断开连接：{request.sid}')


@socketio.on('join_ticket')
def handle_join_ticket(data):
    """加入工单聊天室"""
    ticket_id = data.get('ticket_id')
    user_type = data.get('user_type')  # 'customer' or 'service'
    user_name = data.get('user_name', '匿名用户')

    if ticket_id:
        room = f'ticket_{ticket_id}'
        join_room(room)
        print(f'{user_name} ({user_type}) 加入了工单 {ticket_id} 聊天室')

        # 发送加入通知给房间内其他人
        emit('notification', {
            'message': f'{user_name} 加入了聊天',
            'user_type': user_type
        }, room=room, skip_sid=request.sid)


@socketio.on('leave_ticket')
def handle_leave_ticket(data):
    """离开工单聊天室"""
    ticket_id = data.get('ticket_id')
    user_type = data.get('user_type')
    user_name = data.get('user_name', '匿名用户')

    if ticket_id:
        room = f'ticket_{ticket_id}'
        leave_room(room)
        print(f'{user_name} ({user_type}) 离开了工单 {ticket_id} 聊天室')

        # 发送离开通知给房间内其他人
        emit('notification', {
            'message': f'{user_name} 离开了聊天',
            'user_type': user_type
        }, room=room, skip_sid=request.sid)


@socketio.on('send_message')
def handle_send_message(data):
    """发送消息"""
    ticket_id = data.get('ticket_id')
    sender = data.get('sender')  # 'customer' or 'service'
    sender_name = data.get('sender_name')
    content = data.get('content')

    if not all([ticket_id, sender, sender_name, content]):
        return {'success': False, 'message': '消息参数不完整'}

    try:
        # 保存消息到数据库
        conn = get_db_connection()
        if not conn:
            return {'success': False, 'message': '数据库连接失败'}
        cursor = conn.cursor()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        insert_sql = """
                     INSERT INTO messages (ticket_id, sender, sender_name, content, send_time) \
                     VALUES (%s, %s, %s, %s, %s) \
                     """
        cursor.execute(insert_sql, (ticket_id, sender, sender_name, content, now))
        conn.commit()

        # 获取插入的消息ID
        message_id = cursor.lastrowid
        cursor.close()
        conn.close()

        # 构建消息对象
        message_data = {
            'id': message_id,
            'ticket_id': ticket_id,
            'sender': sender,
            'sender_name': sender_name,
            'content': content,
            'send_time': now
        }

        # 广播消息到工单聊天室
        room = f'ticket_{ticket_id}'
        emit('new_message', message_data, room=room)

        return {'success': True, 'message': '消息发送成功'}
    except Exception as e:
        print(f"发送消息异常：{e}")
        return {'success': False, 'message': f'发送失败：{str(e)}'}


# -------------------------- 静态文件服务 --------------------------
@app.route('/')
def index():
    """首页重定向到登录页"""
    return send_from_directory(FRONTEND_DIR, 'login.html')


@app.route('/<path:filename>')
def serve_frontend(filename):
    """提供前端静态文件"""
    try:
        return send_from_directory(FRONTEND_DIR, filename)
    except:
        return "404 - 文件未找到", 404







# 首次运行初始化数据库表
init_ticket_table()
init_message_table()
init_user_table()

# 启动服务
if __name__ == '__main__':
    # 使用socketio.run替代app.run以支持WebSocket
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)  # 生产环境请将debug改为False