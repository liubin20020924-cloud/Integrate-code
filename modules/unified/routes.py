"""
统一用户管理路由模块
整合知识库和工单系统的用户管理功能
"""
from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
import pymysql
import hashlib
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common.db_manager import get_connection
from werkzeug.security import generate_password_hash, check_password_hash
from modules.unified.utils import get_current_user, login_required

# 创建统一用户管理蓝图
unified_bp = Blueprint('unified', __name__, url_prefix='/unified')


def get_kb_db_connection():
    """获取知识库数据库连接（统一用户表）"""
    return get_connection('kb')


def get_case_db_connection():
    """获取工单数据库连接"""
    return get_connection('case')


def get_unified_users():
    """获取两个系统的所有用户"""
    kb_conn = get_kb_db_connection()
    case_conn = get_case_db_connection()

    if not kb_conn or not case_conn:
        return [], "数据库连接失败"

    try:
        kb_cursor = kb_conn.cursor(pymysql.cursors.DictCursor)
        case_cursor = case_conn.cursor(pymysql.cursors.DictCursor)

        # 获取知识库用户
        kb_cursor.execute("""
            SELECT
                id,
                username,
                display_name,
                role as kb_role,
                email,
                status,
                last_login,
                created_at,
                'knowledge' as system
            FROM mgmt_users
            ORDER BY created_at DESC
        """)
        kb_users = kb_cursor.fetchall()

        # 获取工单用户
        case_cursor.execute("""
            SELECT
                id,
                username,
                real_name as display_name,
                role as case_role,
                email,
                created_time as created_at,
                'case' as system
            FROM users
            ORDER BY create_time DESC
        """)
        case_users = case_cursor.fetchall()

        kb_cursor.close()
        case_cursor.close()
        kb_conn.close()
        case_conn.close()

        # 标记统一用户（在两个系统中都存在的用户）
        kb_usernames = {user['username'] for user in kb_users}
        case_usernames = {user['username'] for user in case_users}

        # 为知识库用户添加工单角色标识
        for user in kb_users:
            user['case_role'] = None
            user['is_unified'] = user['username'] in case_usernames

        # 为工单用户添加知识库角色标识
        for user in case_users:
            user['kb_role'] = None
            user['is_unified'] = user['username'] in kb_usernames

        # 合并用户列表（知识库用户在前）
        unified_users = kb_users + case_users

        return unified_users, None

    except Exception as e:
        print(f"获取用户列表失败: {e}")
        if kb_conn:
            kb_conn.close()
        if case_conn:
            case_conn.close()
        return [], str(e)


# ==================== 统一用户管理页面 ====================
@unified_bp.route('/users')
@login_required(roles=['admin'])
def user_management():
    """统一用户管理页面"""
    users, error = get_unified_users()

    return render_template('unified/user_management.html',
                         users=users,
                         error=error,
                         current_user=get_current_user())


# ==================== 知识库用户管理 ====================
@unified_bp.route('/api/kb-users', methods=['GET'])
@login_required(roles=['admin'])
def get_kb_users():
    """获取知识库用户列表"""
    try:
        connection = get_kb_db_connection()
        if connection is None:
            return jsonify({'success': False, 'message': '数据库连接失败'})

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT
                    id,
                    username,
                    display_name,
                    role,
                    email,
                    status,
                    last_login,
                    login_attempts,
                    created_at,
                    updated_at
                FROM mgmt_users
                ORDER BY created_at DESC
            """)
            users = cursor.fetchall()

        connection.close()

        return jsonify({
            'success': True,
            'data': users,
            'count': len(users)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@unified_bp.route('/api/kb-users', methods=['POST'])
@login_required(roles=['admin'])
def add_kb_user():
    """添加知识库用户"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('username'):
            return jsonify({'success': False, 'message': '用户名不能为空'})

        if not data.get('password'):
            return jsonify({'success': False, 'message': '密码不能为空'})

        connection = get_kb_db_connection()
        if connection is None:
            return jsonify({'success': False, 'message': '数据库连接失败'})

        with connection.cursor() as cursor:
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM mgmt_users WHERE username = %s", (data['username'],))
            if cursor.fetchone():
                connection.close()
                return jsonify({'success': False, 'message': f"用户名 {data['username']} 已存在"})

            # 生成密码哈希
            password_hash = generate_password_hash(data['password'])

            # 插入新用户
            sql = """
            INSERT INTO mgmt_users (username, password_hash, display_name, role, status, email, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data['username'],
                password_hash,
                data.get('display_name', ''),
                data.get('role', 'user'),
                data.get('status', 'active'),
                data.get('email', ''),
                get_current_user()['username']
            ))
            connection.commit()
            user_id = cursor.lastrowid

        connection.close()

        return jsonify({
            'success': True,
            'message': '知识库用户添加成功',
            'user_id': user_id
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f"添加用户时发生错误: {str(e)}"})


@unified_bp.route('/api/kb-users/<int:user_id>', methods=['PUT'])
@login_required(roles=['admin'])
def update_kb_user(user_id):
    """更新知识库用户"""
    try:
        data = request.get_json()

        connection = get_kb_db_connection()
        if connection is None:
            return jsonify({'success': False, 'message': '数据库连接失败'})

        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username FROM mgmt_users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                connection.close()
                return jsonify({'success': False, 'message': f"用户 ID {user_id} 不存在"})

            # 如果是admin用户，不允许修改角色
            if user['username'] == 'admin' and data.get('role') != 'admin':
                connection.close()
                return jsonify({'success': False, 'message': '不能修改管理员admin的角色'})

            # 构建更新SQL
            update_fields = []
            params = []

            if 'display_name' in data:
                update_fields.append("display_name = %s")
                params.append(data['display_name'])

            if 'role' in data:
                update_fields.append("role = %s")
                params.append(data['role'])

            if 'status' in data:
                update_fields.append("status = %s")
                params.append(data['status'])

            if 'email' in data:
                update_fields.append("email = %s")
                params.append(data['email'])

            if 'password' in data and data['password']:
                update_fields.append("password_hash = %s")
                params.append(generate_password_hash(data['password']))

            if not update_fields:
                connection.close()
                return jsonify({'success': False, 'message': '没有提供需要更新的字段'})

            update_fields.append("updated_at = NOW()")
            sql = f"UPDATE mgmt_users SET {', '.join(update_fields)} WHERE id = %s"
            params.append(user_id)

            cursor.execute(sql, params)
            connection.commit()

        connection.close()

        return jsonify({
            'success': True,
            'message': '用户信息更新成功'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f"更新用户时发生错误: {str(e)}"})


@unified_bp.route('/api/kb-users/<int:user_id>', methods=['DELETE'])
@login_required(roles=['admin'])
def delete_kb_user(user_id):
    """删除知识库用户"""
    try:
        connection = get_kb_db_connection()
        if connection is None:
            return jsonify({'success': False, 'message': '数据库连接失败'})

        with connection.cursor() as cursor:
            cursor.execute("SELECT username FROM mgmt_users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                connection.close()
                return jsonify({'success': False, 'message': f"用户 ID {user_id} 不存在"})

            # 不允许删除admin用户
            if user['username'] == 'admin':
                connection.close()
                return jsonify({'success': False, 'message': '不能删除管理员admin'})

            # 删除用户登录日志
            cursor.execute("DELETE FROM mgmt_login_logs WHERE user_id = %s", (user_id,))

            # 删除用户
            cursor.execute("DELETE FROM mgmt_users WHERE id = %s", (user_id,))
            connection.commit()

        connection.close()

        return jsonify({
            'success': True,
            'message': f"用户 {user['username']} 删除成功"
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f"删除用户时发生错误: {str(e)}"})


# ==================== 工单系统用户管理 ====================
@unified_bp.route('/api/case-users', methods=['GET'])
@login_required(roles=['admin'])
def get_case_users():
    """获取工单系统用户列表"""
    try:
        connection = get_case_db_connection()
        if connection is None:
            return jsonify({'success': False, 'message': '数据库连接失败'})

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT
                    id,
                    username,
                    real_name,
                    role,
                    email,
                    create_time
                FROM users
                ORDER BY create_time DESC
            """)
            users = cursor.fetchall()

        connection.close()

        return jsonify({
            'success': True,
            'data': users,
            'count': len(users)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@unified_bp.route('/api/case-users', methods=['POST'])
@login_required(roles=['admin'])
def add_case_user():
    """添加工单系统用户"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('username'):
            return jsonify({'success': False, 'message': '用户名不能为空'})

        if not data.get('password'):
            return jsonify({'success': False, 'message': '密码不能为空'})

        if len(data['password']) < 6:
            return jsonify({'success': False, 'message': '密码长度不能少于6位'})

        connection = get_case_db_connection()
        if connection is None:
            return jsonify({'success': False, 'message': '数据库连接失败'})

        with connection.cursor() as cursor:
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (data['username'],))
            if cursor.fetchone():
                connection.close()
                return jsonify({'success': False, 'message': f"用户名 {data['username']} 已存在"})

            # 检查邮箱是否已存在
            if data.get('email'):
                cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
                if cursor.fetchone():
                    connection.close()
                    return jsonify({'success': False, 'message': f"邮箱 {data['email']} 已被注册"})

            # 生成MD5密码
            password_hash = hashlib.md5(data['password'].encode()).hexdigest()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 插入新用户
            sql = """
            INSERT INTO users (username, password, real_name, role, email, create_time)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data['username'],
                password_hash,
                data.get('real_name', data['username']),
                data.get('role', 'customer'),
                data.get('email', ''),
                now
            ))
            connection.commit()
            user_id = cursor.lastrowid

        connection.close()

        return jsonify({
            'success': True,
            'message': '工单系统用户添加成功',
            'user_id': user_id
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f"添加用户时发生错误: {str(e)}"})


@unified_bp.route('/api/case-users/<int:user_id>', methods=['PUT'])
@login_required(roles=['admin'])
def update_case_user(user_id):
    """更新工单系统用户"""
    try:
        data = request.get_json()

        connection = get_case_db_connection()
        if connection is None:
            return jsonify({'success': False, 'message': '数据库连接失败'})

        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                connection.close()
                return jsonify({'success': False, 'message': f"用户 ID {user_id} 不存在"})

            # 如果是admin用户，不允许修改角色
            if user['username'] == 'admin' and data.get('role') != 'admin':
                connection.close()
                return jsonify({'success': False, 'message': '不能修改管理员admin的角色'})

            # 构建更新SQL
            update_fields = []
            params = []

            if 'real_name' in data:
                update_fields.append("real_name = %s")
                params.append(data['real_name'])

            if 'role' in data:
                update_fields.append("role = %s")
                params.append(data['role'])

            if 'email' in data:
                update_fields.append("email = %s")
                params.append(data['email'])

            if 'password' in data and data['password']:
                if len(data['password']) < 6:
                    connection.close()
                    return jsonify({'success': False, 'message': '密码长度不能少于6位'})
                update_fields.append("password = %s")
                params.append(hashlib.md5(data['password'].encode()).hexdigest())

            if not update_fields:
                connection.close()
                return jsonify({'success': False, 'message': '没有提供需要更新的字段'})

            sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            params.append(user_id)

            cursor.execute(sql, params)
            connection.commit()

        connection.close()

        return jsonify({
            'success': True,
            'message': '用户信息更新成功'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f"更新用户时发生错误: {str(e)}"})


@unified_bp.route('/api/case-users/<int:user_id>', methods=['DELETE'])
@login_required(roles=['admin'])
def delete_case_user(user_id):
    """删除工单系统用户"""
    try:
        connection = get_case_db_connection()
        if connection is None:
            return jsonify({'success': False, 'message': '数据库连接失败'})

        with connection.cursor() as cursor:
            cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                connection.close()
                return jsonify({'success': False, 'message': f"用户 ID {user_id} 不存在"})

            # 不允许删除admin用户
            if user['username'] == 'admin':
                connection.close()
                return jsonify({'success': False, 'message': '不能删除管理员admin'})

            # 删除用户
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            connection.commit()

        connection.close()

        return jsonify({
            'success': True,
            'message': f"用户 {user['username']} 删除成功"
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f"删除用户时发生错误: {str(e)}"})


# ==================== 用户统计 ====================
@unified_bp.route('/api/user-stats', methods=['GET'])
@login_required(roles=['admin'])
def user_stats():
    """获取用户统计信息"""
    try:
        stats = {
            'kb_users': {
                'total': 0,
                'active': 0,
                'admins': 0,
                'users': 0
            },
            'case_users': {
                'total': 0,
                'admins': 0,
                'customers': 0
            },
            'login_logs': {
                'total': 0,
                'today': 0,
                'success': 0,
                'failed': 0
            }
        }

        # 知识库用户统计
        kb_conn = get_kb_db_connection()
        if kb_conn:
            with kb_conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM mgmt_users")
                stats['kb_users']['total'] = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM mgmt_users WHERE status = 'active'")
                stats['kb_users']['active'] = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM mgmt_users WHERE role = 'admin'")
                stats['kb_users']['admins'] = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM mgmt_users WHERE role = 'user'")
                stats['kb_users']['users'] = cursor.fetchone()['count']

                # 登录日志统计
                cursor.execute("SELECT COUNT(*) as count FROM mgmt_login_logs")
                stats['login_logs']['total'] = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM mgmt_login_logs WHERE DATE(login_time) = CURDATE()")
                stats['login_logs']['today'] = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM mgmt_login_logs WHERE status = 'success'")
                stats['login_logs']['success'] = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM mgmt_login_logs WHERE status = 'failed'")
                stats['login_logs']['failed'] = cursor.fetchone()['count']

            kb_conn.close()

        # 工单用户统计
        case_conn = get_case_db_connection()
        if case_conn:
            with case_conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM users")
                stats['case_users']['total'] = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
                stats['case_users']['admins'] = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'customer'")
                stats['case_users']['customers'] = cursor.fetchone()['count']

            case_conn.close()

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
