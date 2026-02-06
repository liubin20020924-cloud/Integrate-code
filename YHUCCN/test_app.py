"""
简单测试脚本 - 验证应用是否能正常启动
"""

import sys
import os

def test_imports():
    """测试所有必要的模块是否可以导入"""
    print("测试1: 检查模块导入...")
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from dotenv import load_dotenv
        print("[OK] 所有依赖模块导入成功")
        return True
    except ImportError as e:
        print(f"[FAIL] 模块导入失败: {e}")
        return False

def test_config():
    """测试配置文件"""
    print("\n测试2: 检查配置文件...")
    try:
        from config_sqlite import Config
        print(f"[OK] 配置加载成功")
        print(f"  - 数据库URI: {Config.SQLALCHEMY_DATABASE_URI}")
        return True
    except Exception as e:
        print(f"[FAIL] 配置加载失败: {e}")
        return False

def test_models():
    """测试数据库模型"""
    print("\n测试3: 检查数据库模型...")
    try:
        from models import ContactMessage
        print("[OK] 数据库模型定义成功")
        return True
    except Exception as e:
        print(f"[FAIL] 数据库模型检查失败: {e}")
        return False

def test_routes():
    """测试路由定义"""
    print("\n测试4: 检查路由定义...")
    try:
        from routes.main import main_bp
        from routes.api import api_bp
        from routes.admin import admin_bp
        print("[OK] 所有路由蓝图定义成功")
        return True
    except Exception as e:
        print(f"[FAIL] 路由检查失败: {e}")
        return False

def test_templates():
    """测试模板文件"""
    print("\n测试5: 检查模板文件...")
    required_files = [
        'templates/base.html',
        'templates/index.html',
        'templates/components/header.html',
        'templates/components/home.html',
        'templates/components/about.html',
        'templates/components/services.html',
        'templates/components/cases.html',
        'templates/components/solutions.html',
        'templates/components/contact.html',
        'templates/components/footer.html',
    ]

    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"[OK] {file_path}")
        else:
            print(f"[FAIL] {file_path} - 文件不存在")
            all_exist = False

    return all_exist

def test_static_files():
    """测试静态文件"""
    print("\n测试6: 检查静态文件...")
    if os.path.exists('jpg'):
        jpg_files = [f for f in os.listdir('jpg') if f.endswith(('.jpg', '.png'))]
        print(f"[OK] jpg文件夹存在，包含 {len(jpg_files)} 个图片文件")
        return True
    else:
        print("[FAIL] jpg文件夹不存在")
        return False

def test_database():
    """测试数据库"""
    print("\n测试7: 检查数据库...")
    if os.path.exists('clouddoors.db'):
        print("[OK] SQLite数据库文件存在")
        return True
    else:
        print("[WARN] SQLite数据库文件不存在，将在首次启动时创建")
        return True  # 不算失败

def test_app_creation():
    """测试应用创建"""
    print("\n测试8: 测试应用创建...")
    try:
        from app_sqlite import create_app
        app = create_app()
        print(f"[OK] Flask应用创建成功")
        print(f"  - 应用名称: {app.name}")
        print(f"  - 调试模式: {app.debug}")
        return True
    except Exception as e:
        print(f"[FAIL] 应用创建失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("云户科技网站 - 应用测试")
    print("=" * 60)

    tests = [
        test_imports,
        test_config,
        test_models,
        test_routes,
        test_templates,
        test_static_files,
        test_database,
        test_app_creation,
    ]

    results = []
    for test in tests:
        result = test()
        results.append(result)

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("\n[OK] 所有测试通过！应用可以正常启动。")
        print("运行 'python app_sqlite.py' 启动应用")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} 个测试失败，请检查错误信息。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
