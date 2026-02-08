-- =====================================================
-- 修复管理员密码脚本
-- 使用场景：数据库已存在但密码哈希不正确
-- =====================================================

USE `YHKB`;

-- 更新 admin 用户的密码为 YHKB@2024
-- 如果 admin 用户不存在，则创建
INSERT INTO `users` (username, password_hash, password_type, display_name, role, status, system, created_by)
VALUES (
    'admin',
    'scrypt:32768:8:1$ZeitszjeQhBOqUJF$dbfa5f57ec9ba38892585302b8ff94cb79a77f9e73644ae32afc12087b2c39d9f3bd254eaff335baca953c4378b8e8b210b5fb9904569fd07b84ca190743b773',
    'werkzeug',
    '系统管理员',
    'admin',
    'active',
    'unified',
    'system'
)
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    password_type = VALUES(password_type),
    status = 'active',
    display_name = VALUES(display_name),
    role = VALUES(role);

-- 验证用户是否存在并状态正常
SELECT
    '用户检查结果' as info,
    id,
    username,
    display_name,
    role,
    status,
    password_type,
    last_login,
    login_attempts,
    created_at
FROM `users`
WHERE username = 'admin';

SELECT '管理员密码已修复！请使用 admin / YHKB@2024 登录' AS status;
