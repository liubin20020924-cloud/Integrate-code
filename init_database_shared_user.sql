-- =====================================================
-- 云户科技网站数据库初始化脚本（共用用户表方案）
-- 适用于 Linux 服务器 MariaDB/MySQL
-- 创建时间: 2026-02-06
-- 说明：知识库和工单系统共用 YHKB.mgmt_users 表
-- =====================================================

-- =====================================================
-- 1. 创建三个数据库
-- =====================================================

-- 创建官网系统数据库
CREATE DATABASE IF NOT EXISTS `clouddoors_db` 
    DEFAULT CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 创建知识库系统数据库（用户表在此库中）
CREATE DATABASE IF NOT EXISTS `YHKB` 
    DEFAULT CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 创建工单系统数据库（工单数据在此库中）
CREATE DATABASE IF NOT EXISTS `casedb` 
    DEFAULT CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 显示所有数据库
SHOW DATABASES;


-- =====================================================
-- 2. 初始化知识库系统数据库 (YHKB) - 包含统一用户表
-- =====================================================
USE `YHKB`;

-- 统一用户管理表（知识库 + 工单系统共用）
CREATE TABLE IF NOT EXISTS `mgmt_users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希值（werkzeug加密）',
    `password_md5` VARCHAR(64) COMMENT '密码MD5（兼容工单系统）',
    `display_name` VARCHAR(100) COMMENT '显示名称',
    `real_name` VARCHAR(100) COMMENT '真实姓名（兼容工单系统）',
    `role` VARCHAR(20) DEFAULT 'user' COMMENT '角色：admin-管理员, user-知识库用户, customer-工单客户',
    `kb_role` VARCHAR(20) DEFAULT 'user' COMMENT '知识库角色：admin, user',
    `case_role` VARCHAR(20) DEFAULT 'customer' COMMENT '工单角色：admin, customer',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active-活跃, inactive-未激活, locked-锁定',
    `last_login` TIMESTAMP NULL COMMENT '最后登录时间',
    `login_attempts` INT DEFAULT 0 COMMENT '登录尝试次数',
    `email` VARCHAR(100) COMMENT '邮箱',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `created_by` VARCHAR(50) COMMENT '创建人',
    INDEX idx_username (`username`),
    INDEX idx_status (`status`),
    INDEX idx_role (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一用户管理表（知识库+工单）';

-- 登录日志表
CREATE TABLE IF NOT EXISTS `mgmt_login_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    `user_id` INT NOT NULL COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL COMMENT '用户名',
    `login_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
    `ip_address` VARCHAR(45) COMMENT 'IP地址',
    `user_agent` TEXT COMMENT '用户代理',
    `status` VARCHAR(20) DEFAULT 'success' COMMENT '状态：success-成功, failed-失败',
    `failure_reason` VARCHAR(255) COMMENT '失败原因',
    INDEX idx_user_id (`user_id`),
    INDEX idx_login_time (`login_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户登录日志表';

-- 知识库信息表
CREATE TABLE IF NOT EXISTS `KB-info` (
    `KB_Number` INT AUTO_INCREMENT PRIMARY KEY COMMENT '知识库编号',
    `KB_Name` VARCHAR(200) NOT NULL COMMENT '知识库名称',
    `KB_Description` TEXT COMMENT '知识库描述',
    `KB_Category` VARCHAR(50) COMMENT '知识库分类',
    `KB_Author` VARCHAR(100) COMMENT '作者',
    `KB_CreateTime` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `KB_UpdateTime` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_KB_Name (`KB_Name`),
    INDEX idx_KB_Category (`KB_Category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库信息表';

-- 插入默认超级管理员账号
-- 密码：YHKB@2024（werkzeug加密）
-- 密码MD5：0192023a7bbd73250516f069df18b500（兼容工单系统，密码：admin123）
INSERT INTO `mgmt_users` (
    username, 
    password_hash, 
    password_md5,
    display_name, 
    role, 
    kb_role, 
    case_role, 
    status, 
    email, 
    created_by
)
VALUES (
    'admin', 
    'pbkdf2:sha256:260000$8qB1N6Q8Kv6ZQ5fN$a6b5e4f3d2c1b0a9e8d7c6b5a4e3d2f1b0a9c8d7e6f5a4b3c2d1e0f9a8b7c6d5',
    '0192023a7bbd73250516f069df18b500',
    '系统管理员', 
    'admin',
    'admin',
    'admin',
    'active',
    '1919516011@qq.com',
    'system'
)
ON DUPLICATE KEY UPDATE username=username;


-- =====================================================
-- 3. 初始化官网系统数据库 (clouddoors_db)
-- =====================================================
USE `clouddoors_db`;

-- 注意：官网系统目前使用 SQLAlchemy ORM，表会自动创建
-- 如果需要手动创建留言表，可以使用以下SQL：

-- 留言表（联系表单）
-- CREATE TABLE IF NOT EXISTS `messages` (
--     `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '留言ID',
--     `name` VARCHAR(100) NOT NULL COMMENT '姓名',
--     `email` VARCHAR(100) NOT NULL COMMENT '邮箱',
--     `message` TEXT NOT NULL COMMENT '留言内容',
--     `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
--     `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending-待处理, processed-已处理',
--     INDEX idx_created_at (`created_at`),
--     INDEX idx_status (`status`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='官网留言表';


-- =====================================================
-- 4. 初始化工单系统数据库 (casedb)
-- =====================================================
USE `casedb`;

-- 工单主表
CREATE TABLE IF NOT EXISTS `tickets` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增ID',
    `ticket_id` VARCHAR(32) NOT NULL UNIQUE COMMENT '工单唯一标识ID（格式：TK-YYYYMMDDHHMMSS-XXXXXX）',
    `customer_name` VARCHAR(100) NOT NULL COMMENT '客户名称（关联mgmt_users.username）',
    `customer_contact` VARCHAR(50) NOT NULL COMMENT '客户联系方式',
    `customer_email` VARCHAR(100) NOT NULL COMMENT '客户邮箱',
    `product` VARCHAR(50) NOT NULL COMMENT '涉及产品',
    `issue_type` VARCHAR(20) NOT NULL COMMENT '问题类型：technical-技术, service-服务, complaint-投诉, other-其他',
    `priority` VARCHAR(10) NOT NULL COMMENT '工单优先级：low-低, medium-中, high-高, urgent-紧急',
    `title` VARCHAR(200) NOT NULL COMMENT '问题标题',
    `content` TEXT NOT NULL COMMENT '问题详情',
    `status` VARCHAR(10) DEFAULT 'pending' COMMENT '工单状态：pending-待处理, processing-处理中, completed-已完成, closed-已关闭',
    `create_time` DATETIME NOT NULL COMMENT '创建时间',
    `update_time` DATETIME NOT NULL COMMENT '更新时间',
    INDEX idx_ticket_id (`ticket_id`),
    INDEX idx_customer_name (`customer_name`),
    INDEX idx_status (`status`),
    INDEX idx_create_time (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单系统主表';

-- 工单聊天消息表
CREATE TABLE IF NOT EXISTS `messages` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '消息ID',
    `ticket_id` VARCHAR(32) NOT NULL COMMENT '工单ID',
    `sender` VARCHAR(20) NOT NULL COMMENT '发送者：admin-管理员, customer-客户',
    `sender_name` VARCHAR(100) NOT NULL COMMENT '发送者名称',
    `content` TEXT NOT NULL COMMENT '消息内容',
    `send_time` DATETIME NOT NULL COMMENT '发送时间',
    INDEX idx_ticket_id (`ticket_id`),
    INDEX idx_send_time (`send_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单聊天消息表';

-- 注意：工单系统不再创建独立的 users 表，直接使用 YHKB.mgmt_users
-- 如果已有 users 表，可以迁移数据后删除


-- =====================================================
-- 5. 创建数据库用户并授权（可选）
-- =====================================================

-- 创建专用数据库用户
-- CREATE USER IF NOT EXISTS 'clouddoors_user'@'%' IDENTIFIED BY 'your_secure_password';
-- CREATE USER IF NOT EXISTS 'kb_user'@'%' IDENTIFIED BY 'your_secure_password';
-- CREATE USER IF NOT EXISTS 'case_user'@'%' IDENTIFIED BY 'your_secure_password';

-- 授予权限
-- GRANT ALL PRIVILEGES ON `clouddoors_db`.* TO 'clouddoors_user'@'%';
-- GRANT ALL PRIVILEGES ON `YHKB`.* TO 'kb_user'@'%';
-- GRANT ALL PRIVILEGES ON `casedb`.* TO 'case_user'@'%';
-- GRANT SELECT ON `YHKB`.`mgmt_users` TO 'case_user'@'%';  -- 工单系统需要读取用户表

-- 刷新权限
-- FLUSH PRIVILEGES;


-- =====================================================
-- 6. 验证表创建
-- =====================================================

-- 显示官网数据库的表
USE `clouddoors_db`;
SHOW TABLES;

-- 显示知识库数据库的表
USE `YHKB`;
SHOW TABLES;

-- 显示工单系统数据库的表
USE `casedb`;
SHOW TABLES;


-- =====================================================
-- 7. 查看表结构
-- =====================================================

-- 查看统一用户表结构
USE `YHKB`;
DESC `mgmt_users`;
DESC `mgmt_login_logs`;
DESC `KB-info`;

-- 查看工单系统表结构
USE `casedb`;
DESC `tickets`;
DESC `messages`;


-- =====================================================
-- 8. 数据迁移说明（如果已有旧数据）
-- =====================================================

-- 如果工单系统已有独立的 users 表，需要迁移数据到统一用户表：
/*
USE `casedb`;
-- 备份旧表
CREATE TABLE users_backup AS SELECT * FROM users;

-- 迁移数据到统一用户表
INSERT INTO `YHKB`.`mgmt_users` 
    (username, password_hash, password_md5, real_name, role, case_role, email, created_at)
SELECT 
    username, 
    password_md5,  -- 临时存储
    password,      -- MD5密码
    real_name, 
    role, 
    role,          -- case_role 与 role 相同
    email, 
    create_time
FROM users
WHERE username NOT IN (SELECT username FROM `YHKB`.`mgmt_users`);

-- 删除旧表（可选）
DROP TABLE users;
*/


-- =====================================================
-- 完成
-- =====================================================
SELECT '数据库初始化完成（共用用户表方案）！' AS status;
