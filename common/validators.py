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


def validate_password(password: str) -> Tuple[bool, str]:
    """
    验证密码强度
    
    Args:
        password: 密码
        
    Returns:
        (is_valid, error_message)
    """
    if not password:
        return False, "密码不能为空"
    
    if len(password) < 6:
        return False, "密码长度至少6位"
    
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
    
    # 验证密码
    if 'password' in data:
        is_valid, msg = validate_password(data['password'])
        if not is_valid:
            errors['password'] = msg
    
    # 验证角色
    if 'role' in data:
        valid_roles = ['admin', 'user', 'editor']
        if data['role'] not in valid_roles:
            errors['role'] = f"角色必须是 {', '.join(valid_roles)} 之一"
    
    # 验证状态
    if 'status' in data:
        valid_statuses = ['active', 'inactive', 'locked']
        if data['status'] not in valid_statuses:
            errors['status'] = f"状态必须是 {', '.join(valid_statuses)} 之一"
    
    return len(errors) == 0, errors
