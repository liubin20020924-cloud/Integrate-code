# 文档目录

本目录包含云户科技网站项目的所有文档文件。

## 系统说明文档

### [官网系统说明](./HOME_SYSTEM_GUIDE.md)
详细介绍官网系统的架构、功能、API接口和部署方法。
- 官网系统架构和功能介绍
- 数据库设计和API接口
- 部署和维护指南
- 故障排除和安全建议

### [知识库系统说明](./KB_SYSTEM_GUIDE.md)
详细介绍知识库系统的架构、功能、认证和Trilium集成。
- 知识库系统架构和功能介绍
- 用户认证和权限管理
- Trilium集成配置
- 数据库设计和API接口

### [工单系统说明](./CASE_SYSTEM_GUIDE.md)
详细介绍工单系统的架构、功能、实时聊天和邮件通知。
- 工单系统架构和功能介绍
- 实时聊天和WebSocket
- 邮件通知和附件管理
- 数据库设计和API接口

### [统一用户管理系统说明](./UNIFIED_SYSTEM_GUIDE.md)
详细介绍统一用户管理系统的架构和功能。
- 统一用户管理系统架构
- 用户管理功能详解
- API接口和安全配置
- 部署和使用指南

## 用户管理相关

### [统一用户管理系统详细指南](./UNIFIED_USER_MANAGEMENT.md)
- 详细介绍统一用户管理系统的功能和使用方法
- API 接口说明
- 部署步骤和故障排查

### [用户表整合修改指南](./MERGE_USERS_GUIDE.md)
- 可选方案：如何将知识库和工单系统的用户表合并
- 代码修改步骤
- 数据迁移脚本

### [统一用户管理系统实施总结](./UNIFIED_IMPLEMENTATION_SUMMARY.md)
- 已完成的工作总结
- 功能清单
- 技术特点和后续优化建议

## 开发相关

### [代码风格指南](./STYLE_GUIDE.md)
- 项目代码规范
- 命名约定
- 最佳实践

## 项目总览

### [项目 README](../README.md)
- 项目介绍
- 系统架构
- 快速开始指南

## 数据库脚本

数据库初始化脚本位于项目根目录：

- `init_database.sql` - 标准数据库初始化（独立用户表）
- `init_database_shared_user.sql` - 共用用户表版本（可选）

## 项目结构

```
Integrate-code/
├── README.md                      # 项目总览和快速开始指南
├── STYLE_GUIDE.md                 # 代码风格指南
├── init_database.sql              # 数据库初始化脚本
├── init_database_shared_user.sql  # 共用用户表版本（可选）
├── requirements.txt              # Python依赖
├── start.bat                     # Windows启动脚本
├── start.sh                      # Linux启动脚本
├── docs/                         # 文档目录（本目录）
│   ├── README.md                  # 本文件
│   ├── HOME_SYSTEM_GUIDE.md       # 官网系统说明
│   ├── KB_SYSTEM_GUIDE.md         # 知识库系统说明
│   ├── CASE_SYSTEM_GUIDE.md       # 工单系统说明
│   ├── UNIFIED_SYSTEM_GUIDE.md    # 统一用户管理说明
│   ├── UNIFIED_USER_MANAGEMENT.md # 统一用户管理详细指南
│   ├── MERGE_USERS_GUIDE.md      # 用户表合并指南
│   ├── UNIFIED_IMPLEMENTATION_SUMMARY.md  # 实施总结
│   └── STYLE_GUIDE.md            # 代码风格指南
├── modules/                      # 应用模块
│   ├── case/                     # 工单系统
│   ├── kb/                       # 知识库系统
│   ├── home/                     # 官网系统
│   └── unified/                  # 统一用户管理
├── templates/                    # 模板文件
├── static/                       # 静态资源
├── common/                       # 公共模块
└── instance/                     # SQLite数据库文件（官网）
```

## 更新日志

### 2026-02-06 (系统说明文档)
- 创建官网系统说明文档
- 创建知识库系统说明文档
- 创建工单系统说明文档
- 创建统一用户管理说明文档
- 更新文档索引

### 2026-02-06 (目录重组)
- 将 `website/` 目录下的所有文件移动到项目根目录
- 删除 `website/` 目录
- 更新所有代码中的路径引用
- 项目结构更简洁，便于部署

### 2026-02-06 (文档重组)
- 创建文档目录
- 移动所有 MD 文档到 `docs/` 目录
- 保留 `README.md` 在项目根目录
- 添加本说明文件

## 快速导航

### 新手入门
1. [项目总览](../README.md) - 了解项目概况
2. [快速开始](../README.md#快速启动) - 快速启动项目
3. [官网系统说明](./HOME_SYSTEM_GUIDE.md) - 了解官网系统
4. [知识库系统说明](./KB_SYSTEM_GUIDE.md) - 了解知识库系统
5. [工单系统说明](./CASE_SYSTEM_GUIDE.md) - 了解工单系统
6. [统一用户管理说明](./UNIFIED_SYSTEM_GUIDE.md) - 了解用户管理

### 开发人员
1. [代码风格指南](./STYLE_GUIDE.md) - 代码规范
2. [官网系统API](./HOME_SYSTEM_GUIDE.md#api接口)
3. [知识库系统API](./KB_SYSTEM_GUIDE.md#api接口)
4. [工单系统API](./CASE_SYSTEM_GUIDE.md#api接口)
5. [统一用户管理API](./UNIFIED_SYSTEM_GUIDE.md#api接口)

### 运维人员
1. [官网系统部署](./HOME_SYSTEM_GUIDE.md#部署说明)
2. [知识库系统部署](./KB_SYSTEM_GUIDE.md#部署说明)
3. [工单系统部署](./CASE_SYSTEM_GUIDE.md#部署说明)
4. [统一用户管理部署](./UNIFIED_SYSTEM_GUIDE.md#部署说明)
5. [故障排除](./CASE_SYSTEM_GUIDE.md#故障排除)

## 常见问题

### 如何启动项目？
参考 [项目总览](../README.md) 的快速启动部分。

### 如何配置数据库？
参考各个系统说明文档的部署说明部分：
- [官网系统数据库配置](./HOME_SYSTEM_GUIDE.md#数据库配置)
- [知识库系统数据库配置](./KB_SYSTEM_GUIDE.md#数据库配置)
- [工单系统数据库配置](./CASE_SYSTEM_GUIDE.md#数据库配置)

### 默认账号是什么？
- 知识库系统: admin / YHKB@2024
- 工单系统: admin / admin123

详见各系统说明文档的"默认账号"部分。

### 如何部署到Linux服务器？
参考各个系统说明文档的"部署说明"部分，或使用项目根目录的启动脚本 `start.sh`。

## 联系方式

如有问题或建议，请联系：
- 邮箱: dora.dong@cloud-doors.com
- 工单系统: http://your-server:5000/case
