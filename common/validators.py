"""
输入验证模块
提供常用的输入验证函数
"""
import re
from typing import Dict, List, Optional, Any, Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        (is_valid, error_message)
    """
    if not email:
        return False, "邮箱不能为空"
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "邮箱格式不正确"
    
    return True, ""


def validate_password(password: str, is_admin: bool = False) -> Tuple[bool, str]:
    """
    验证密码强度（增强版）

    Args:
        password: 密码
        is_admin: 是否为管理员密码（管理员密码要求更高）

    Returns:
        (is_valid, error_message)
    """
    if not password:
        return False, "密码不能为空"

    # 基础要求
    min_length = 8 if is_admin else 8
    if len(password) < min_length:
        return False, f"密码长度至少{min_length}位"

    # 管理员密码更严格
    if is_admin:
        # 必须包含大小写字母、数字和特殊字符
        if not re.search(r'[A-Z]', password):
            return False, "密码必须包含至少一个大写字母"
        if not re.search(r'[a-z]', password):
            return False, "密码必须包含至少一个小写字母"
        if not re.search(r'[0-9]', password):
            return False, "密码必须包含至少一个数字"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "密码必须包含至少一个特殊字符（!@#$%^&*等）"
        if len(password) < 10:
            return False, "管理员密码长度至少10位"
    else:
        # 普通用户密码：至少包含字母和数字
        has_letter = re.search(r'[a-zA-Z]', password)
        has_digit = re.search(r'[0-9]', password)
        if not (has_letter and has_digit):
            return False, "密码必须同时包含字母和数字"

        # 推荐包含特殊字符（但不强制）
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            # 只返回警告，不返回错误
            pass

    # 检查常见弱密码
    weak_passwords = [
        '123456', 'password', 'qwerty', 'abc123', '111111',
        '12345678', '123456789', 'admin123', 'password123',
        'YHKB@2024', 'admin@2024', 'root123'
    ]
    if password.lower() in weak_passwords:
        return False, "密码过于简单，请使用更复杂的密码"

    # 检查是否为纯数字或纯字母
    if password.isdigit():
        return False, "密码不能为纯数字"
    if password.isalpha():
        return False, "密码不能为纯字母"

    # 检查重复字符
    if len(set(password)) < 4:
        return False, "密码不能包含过多重复字符"

    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """
    验证用户名
    
    Args:
        username: 用户名
        
    Returns:
        (is_valid, error_message)
    """
    if not username:
        return False, "用户名不能为空"
    
    if len(username) < 3:
        return False, "用户名长度至少3位"
    
    if len(username) > 32:
        return False, "用户名长度不能超过32位"
    
    # 只允许字母、数字、下划线
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    
    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    验证手机号
    
    Args:
        phone: 手机号
        
    Returns:
        (is_valid, error_message)
    """
    if not phone:
        return True, ""  # 手机号可以为空
    
    # 中国大陆手机号
    phone_pattern = r'^1[3-9]\d{9}$'
    if not re.match(phone_pattern, phone):
        return False, "手机号格式不正确"
    
    return True, ""


def validate_required(data: Dict, required_fields: List[str]) -> Tuple[bool, Dict[str, str]]:
    """
    验证必填字段
    
    Args:
        data: 数据字典
        required_fields: 必填字段列表
        
    Returns:
        (is_valid, errors)
    """
    errors = {}
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            errors[field] = f"{field} 是必填字段"
    
    return len(errors) == 0, errors


def validate_user_data(data: Dict) -> Tuple[bool, Dict[str, str]]:
    """
    验证用户数据

    Args:
        data: 用户数据字典

    Returns:
        (is_valid, errors)
    """
    errors = {}

    # 验证用户名
    if 'username' in data:
        is_valid, msg = validate_username(data['username'])
        if not is_valid:
            errors['username'] = msg

    # 验证邮箱
    if 'email' in data:
        is_valid, msg = validate_email(data['email'])
        if not is_valid:
            errors['email'] = msg

    # 验证手机号
    if 'phone' in data:
        is_valid, msg = validate_phone(data['phone'])
        if not is_valid:
            errors['phone'] = msg

    # 验证密码（根据角色选择强度）
    if 'password' in data:
        is_admin = data.get('role') == 'admin'
        is_valid, msg = validate_password(data['password'], is_admin=is_admin)
        if not is_valid:
            errors['password'] = msg

    # 验证角色
    if 'role' in data:
        valid_roles = ['admin', 'user', 'editor', 'customer']
        if data['role'] not in valid_roles:
            errors['role'] = f"角色必须是 {', '.join(valid_roles)} 之一"

    # 验证状态
    if 'status' in data:
        valid_statuses = ['active', 'inactive', 'locked']
        if data['status'] not in valid_statuses:
            errors['status'] = f"状态必须是 {', '.join(valid_statuses)} 之一"

    # 验证确认密码（如果提供）
    if 'confirm_password' in data and 'password' in data:
        if data['password'] != data['confirm_password']:
            errors['confirm_password'] = "两次输入的密码不一致"

    return len(errors) == 0, errors
