# 初始化数据库
from app import create_app, db
from models import ContactMessage

app = create_app()

with app.app_context():
    # 创建所有表
    db.create_all()
    print("数据库表创建成功！")

    # 检查表是否存在
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"已创建的表: {tables}")
