"""表单验证辅助函数"""

import re

def sanitize_input(input_str):
    """
    安全过滤输入
    :param input_str: 输入字符串
    :return: 过滤后的字符串
    """
    if not input_str:
        return ""
    # 去除空格
    input_str = input_str.strip()
    # 去除HTML标签
    input_str = re.sub(r'<[^>]+>', '', input_str)
    # 转义特殊字符（Flask/Jinja2会自动处理）
    return input_str

def validate_phone(phone):
    """
    验证电话号码（中国手机号）
    :param phone: 电话号码
    :return: 是否有效
    """
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))

def validate_email(email):
    """
    验证邮箱地址
    :param email: 邮箱地址
    :return: 是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_contact_form(data):
    """
    验证联系表单数据
    :param data: 表单数据字典
    :return: (is_valid, errors) 是否有效和错误列表
    """
    errors = []

    # 验证姓名
    name = data.get('name', '').strip()
    if not name:
        errors.append('姓名不能为空')

    # 验证电话
    phone = data.get('phone', '').strip()
    if not phone:
        errors.append('电话不能为空')
    elif not validate_phone(phone):
        errors.append('电话号码格式不正确')

    # 验证邮箱（如果提供）
    email = data.get('email', '').strip()
    if email and not validate_email(email):
        errors.append('邮箱格式不正确')

    # 验证留言内容
    message = data.get('message', '').strip()
    if not message:
        errors.append('留言内容不能为空')

    return len(errors) == 0, errors
