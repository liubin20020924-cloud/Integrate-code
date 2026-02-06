from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ContactMessage(db.Model):
    """联系留言模型"""
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='姓名')
    phone = db.Column(db.String(20), nullable=False, comment='电话')
    email = db.Column(db.String(100), nullable=True, comment='邮箱')
    message = db.Column(db.Text, nullable=False, comment='留言内容')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1-未处理, 2-已联系, 3-已完成')

    def __repr__(self):
        return f'<ContactMessage {self.id}: {self.name}>'

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'message': self.message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'status': self.status
        }

    @staticmethod
    def validate_phone(phone):
        """验证中国手机号"""
        import re
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))

    @staticmethod
    def validate_email(email):
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
