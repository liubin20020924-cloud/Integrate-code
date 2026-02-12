-- 创建新的数据库用户用于应用连接
-- 用户名: appuser, 密码: apppass123

-- 创建用户
CREATE USER IF NOT EXISTS 'appuser'@'localhost' IDENTIFIED BY 'apppass123';

-- 授予三个数据库的所有权限
GRANT ALL PRIVILEGES ON clouddoors_db.* TO 'appuser'@'localhost';
GRANT ALL PRIVILEGES ON YHKB.* TO 'appuser'@'localhost';
GRANT ALL PRIVILEGES ON casedb.* TO 'appuser'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 显示用户
SELECT User, Host FROM mysql.user WHERE User = 'appuser';

SELECT '========================================' AS info;
SELECT '数据库用户创建成功！' AS status;
SELECT '========================================' AS info;
SELECT '用户名: appuser' AS info;
SELECT '密码: apppass123' AS info;
SELECT '========================================' AS info;
