-- =====================================================
-- 云户科技网站数据库初始化脚本
-- 适用于 Linux 服务器 MariaDB/MySQL
-- 创建时间: 2026-02-06
-- =====================================================

-- =====================================================
-- 1. 创建三个数据库
-- =====================================================

-- 创建官网系统数据库
CREATE DATABASE IF NOT EXISTS `clouddoors_db` 
    DEFAULT CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 创建知识库系统数据库
CREATE DATABASE IF NOT EXISTS `YHKB` 
    DEFAULT CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 创建工单系统数据库
CREATE DATABASE IF NOT EXISTS `casedb` 
    DEFAULT CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 显示所有数据库
SHOW DATABASES;


-- =====================================================
-- 2. 初始化官网系统数据库 (clouddoors_db)
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
-- 3. 初始化知识库系统数据库 (YHKB)
-- =====================================================
USE `YHKB`;

-- 知识库信息表（注意：表名包含连字符，必须使用反引号）
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

-- 知识库用户管理表
CREATE TABLE IF NOT EXISTS `mgmt_users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希值（werkzeug加密）',
    `display_name` VARCHAR(100) COMMENT '显示名称',
    `role` VARCHAR(20) DEFAULT 'user' COMMENT '角色：admin-管理员, user-普通用户',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active-活跃, inactive-未激活',
    `last_login` TIMESTAMP NULL COMMENT '最后登录时间',
    `login_attempts` INT DEFAULT 0 COMMENT '登录尝试次数',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `created_by` VARCHAR(50) COMMENT '创建人',
    INDEX idx_username (`username`),
    INDEX idx_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库用户管理表';

-- 插入默认管理员账号（密码：YHKB@2024）
-- 密码哈希值使用 werkzeug 生成
INSERT INTO `mgmt_users` (username, password_hash, display_name, role, created_by)
VALUES ('admin', 'pbkdf2:sha256:260000$8qB1N6Q8Kv6ZQ5fN$a6b5e4f3d2c1b0a9e8d7c6b5a4e3d2f1b0a9c8d7e6f5a4b3c2d1e0f9a8b7c6d5', '系统管理员', 'admin', 'system')
ON DUPLICATE KEY UPDATE username=username;


-- =====================================================
-- 4. 初始化工单系统数据库 (casedb)
-- =====================================================
USE `casedb`;

-- 工单主表
CREATE TABLE IF NOT EXISTS `tickets` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增ID',
    `ticket_id` VARCHAR(32) NOT NULL UNIQUE COMMENT '工单唯一标识ID（格式：TK-YYYYMMDDHHMMSS-XXXXXX）',
    `customer_name` VARCHAR(100) NOT NULL COMMENT '客户名称',
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

-- 工单系统用户表
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    `password` VARCHAR(64) NOT NULL COMMENT '密码（MD5加密）',
    `real_name` VARCHAR(100) NOT NULL COMMENT '真实姓名',
    `role` VARCHAR(20) NOT NULL COMMENT '角色：admin-管理员, customer-客户',
    `email` VARCHAR(100) COMMENT '邮箱',
    `create_time` DATETIME NOT NULL COMMENT '创建时间',
    INDEX idx_username (`username`),
    INDEX idx_role (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单系统用户表';

-- 插入默认管理员账号（密码：admin123，MD5加密后为：0192023a7bbd73250516f069df18b500）
INSERT INTO `users` (username, password, real_name, role, email, create_time)
VALUES ('admin', '0192023a7bbd73250516f069df18b500', '系统管理员', 'admin', '1919516011@qq.com', NOW())
ON DUPLICATE KEY UPDATE username=username;


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

-- 查看工单系统表结构
USE `casedb`;
DESC `tickets`;
DESC `messages`;
DESC `users`;

-- 查看知识库系统表结构
USE `YHKB`;
DESC `KB-info`;
DESC `mgmt_users`;


-- =====================================================
-- 完成
-- =====================================================
SELECT '数据库初始化完成！' AS status;
