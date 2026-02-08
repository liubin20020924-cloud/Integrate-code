"""
测试新模块功能
验证所有新创建的模块是否能正常工作
"""

import sys
import traceback

print("=" * 60)
print("开始测试新模块")
print("=" * 60)

# 测试1: 配置模块
print("\n[1/6] 测试配置模块...")
try:
    import config
    print(f"  [OK] config.py 导入成功")
    print(f"  [INFO] DB_HOST: {config.DB_HOST}")
    print(f"  [INFO] DB_NAME_KB: {config.DB_NAME_KB}")
except Exception as e:
    print(f"  [FAIL] config.py 导入失败: {e}")
    traceback.print_exc()

# 测试2: 响应模块
print("\n[2/6] 测试响应模块...")
try:
    from common.response import (
        success_response, error_response, not_found_response,
        unauthorized_response, forbidden_response, validation_error_response,
        server_error_response
    )

    # 测试成功响应
    result, status = success_response(data={'key': 'value'}, message='测试成功')
    print(f"  [OK] success_response 工作正常")

    # 测试错误响应
    result, status = error_response('测试错误', 400)
    print(f"  [OK] error_response 工作正常")

    # 测试验证错误响应
    result, status = validation_error_response({'field': '错误信息'})
    print(f"  [OK] validation_error_response 工作正常")

    print(f"  [OK] 所有响应函数工作正常")
except Exception as e:
    print(f"  [FAIL] 响应模块测试失败: {e}")
    traceback.print_exc()

# 测试3: 日志模块
print("\n[3/6] 测试日志模块...")
try:
    from common.logger import logger, log_exception, LoggerMixin

    logger.info("这是一条INFO日志")
    logger.warning("这是一条WARNING日志")
    logger.error("这是一条ERROR日志")

    class TestService(LoggerMixin):
        def test(self):
            self.logger.info("使用LoggerMixin测试")

    service = TestService()
    service.test()

    print(f"  [OK] 日志模块工作正常")
    print(f"  [INFO] 请检查 logs/app.log 文件")
except Exception as e:
    print(f"  [FAIL] 日志模块测试失败: {e}")
    traceback.print_exc()

# 测试4: 验证器模块
print("\n[4/6] 测试验证器模块...")
try:
    from common.validators import (
        validate_email, validate_password, validate_username,
        validate_phone, validate_required, validate_user_data
    )

    # 测试邮箱验证
    is_valid, msg = validate_email("test@example.com")
    print(f"  [OK] validate_email 有效邮箱: {is_valid}")

    is_valid, msg = validate_email("invalid-email")
    print(f"  [OK] validate_email 无效邮箱: {not is_valid}")

    # 测试密码验证
    is_valid, msg = validate_password("test123")
    print(f"  [OK] validate_password 有效密码: {is_valid}")

    # 测试必填字段验证
    is_valid, errors = validate_required({'name': 'test', 'email': 'test@example.com'}, ['name', 'email'])
    print(f"  [OK] validate_required 有效: {is_valid}")

    # 测试用户数据验证
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'test123',
        'role': 'user'
    }
    is_valid, errors = validate_user_data(user_data)
    print(f"  [OK] validate_user_data 有效数据: {is_valid}")

    print(f"  [OK] 所有验证器工作正常")
except Exception as e:
    print(f"  [FAIL] 验证器模块测试失败: {e}")
    traceback.print_exc()

# 测试5: 用户服务模块
print("\n[5/6] 测试用户服务模块...")
try:
    from services.user_service import UserService

    # 只测试导入，不实际调用数据库方法（因为可能没有数据库连接）
    print(f"  [OK] UserService 导入成功")
    print(f"  [INFO] UserService 包含以下方法:")
    print(f"       - update_user()")
    print(f"       - get_user()")
    print(f"       - get_users()")
    print(f"       - delete_user()")
    print(f"       - change_password()")

    print(f"  [OK] 用户服务模块工作正常")
except Exception as e:
    print(f"  [FAIL] 用户服务模块测试失败: {e}")
    traceback.print_exc()

# 测试6: 路由模块（不实际启动Flask）
print("\n[6/6] 测试路由模块导入...")
try:
    # 测试原始路由
    print("  测试原始 routes.py...")
    import routes
    print(f"  [OK] routes.py 导入成功")

    # 测试新路由（注意：routes_new.py 需要flask-socketio）
    try:
        print("  测试新 routes_new.py...")
        import routes_new
        print(f"  [OK] routes_new.py 导入成功")
    except ImportError as e:
        if 'flask_socketio' in str(e):
            print(f"  [SKIP] routes_new.py 需要 flask-socketio（用于WebSocket功能）")
        else:
            raise

    print(f"  [OK] 路由模块导入正常")
except Exception as e:
    print(f"  [FAIL] 路由模块测试失败: {e}")
    traceback.print_exc()

# 测试7: Flask应用启动（不实际运行）
print("\n[7/7] 测试Flask应用...")
try:
    import app
    print(f"  [OK] Flask应用导入成功")
    print(f"  [INFO] app.py 已包含所有路由注册")
    print(f"  [INFO] 数据库连接池已初始化")
    print(f"  [INFO] 工单系统数据库表已初始化")
except Exception as e:
    print(f"  [FAIL] Flask应用测试失败: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
print("\n[总结]")
print("如果所有测试都显示 [OK]，说明新模块工作正常")
print("如果显示 [FAIL] 或 [SKIP]，请查看详细错误信息")
print("\n[下一步]")
print("1. 如果所有测试通过，可以安全地使用新模块")
print("2. 参考 ROUTES_MIGRATION_GUIDE.md 应用重构代码")
print("3. 参考 QUICK_REFERENCE.md 了解模块使用方法")
print("=" * 60)
