# 云户科技网站 - 文档中心

> 项目文档索引和快速导航指南

---

## 📚 文档列表

### 快速开始

| 文档 | 说明 | 适用场景 |
|--------|------|----------|
| [快速开始指南](../README.md) | 项目简介、安装配置、快速上手 | 新用户入门 |
| [更新日志](../README.md#-更新日志) | 版本更新历史 | 了解最新功能 |

### 系统指南

| 文档 | 说明 | 目标读者 |
|--------|------|----------|
| [官网系统指南](./HOME_SYSTEM_GUIDE.md) | 官网系统功能说明和使用 | 所有用户 |
| [知识库系统指南](./KB_SYSTEM_GUIDE.md) | 知识库浏览、搜索、管理 | 知识库用户 |
| [工单系统指南](./CASE_SYSTEM_GUIDE.md) | 工单创建、聊天、跟踪 | 客户/服务人员 |
| [统一用户管理指南](./UNIFIED_SYSTEM_GUIDE.md) | 用户管理、权限控制 | 管理员 |

### API 文档

| 文档 | 说明 | 端口 |
|--------|------|------|
| [API 文档](./API_DOCS.md) | RESTful API 接口说明 | 开发者 |
| [Trilium 集成](./trilium-py-README.md) | Trilium 笔记服务集成 | 知识库开发者 |

### 安全与优化

| 文档 | 说明 | 适用场景 |
|--------|------|----------|
| [安全改进文档](./SECURITY_IMPROVEMENTS.md) | 安全特性和最佳实践 | 安全审计 |
| [优化计划](./OPTIMIZATION_PLAN.md) | 性能优化和架构改进 | 开发者 |
| [代码统计](./CODE_STATISTICS.md) | 代码量和技术栈分析 | 项目评估 |
| [知识库管理优化](./KB_MANAGEMENT_OPTIMIZATION.md) | 知识库管理功能更新和修复 | 知识库开发者 |

---

## 🗂 文档结构

```
docs/
├── README.md                  # 本文件 - 文档索引
├── HOME_SYSTEM_GUIDE.md       # 官网系统完整指南
├── KB_SYSTEM_GUIDE.md         # 知识库系统完整指南
├── CASE_SYSTEM_GUIDE.md       # 工单系统完整指南
├── UNIFIED_SYSTEM_GUIDE.md    # 统一用户管理完整指南
├── API_DOCS.md               # RESTful API 文档
├── trilium-py-README.md     # Trilium 集成文档
├── OPTIMIZATION_PLAN.md       # 优化计划文档
├── SECURITY_IMPROVEMENTS.md  # 安全特性说明
├── CODE_STATISTICS.md         # 代码统计信息
└── KB_MANAGEMENT_OPTIMIZATION.md  # 知识库管理优化
```

---

## 📖 文档阅读顺序

### 新用户

1. 阅读主项目 [README.md](../README.md)
2. 根据 [快速开始](../README.md#-快速开始) 完成安装配置
3. 阅读 [系统指南](#-系统指南) 了解对应系统功能
4. 参考 [安全改进文档](./SECURITY_IMPROVEMENTS.md) 配置生产环境

### 开发者

1. 阅读 [主 README](../README.md) 了解项目结构
2. 查阅 [API 文档](./API_DOCS.md) 了解接口规范
3. 参考 [优化计划](./OPTIMIZATION_PLAN.md) 了解架构设计
4. 查看 [代码统计](./CODE_STATISTICS.md) 了解技术栈

### 管理员

1. 阅读 [主 README](../README.md) 了解默认账号和配置
2. 查看 [统一用户管理指南](./UNIFIED_SYSTEM_GUIDE.md) 学习用户管理
3. 参考 [安全改进文档](./SECURITY_IMPROVEMENTS.md) 了解安全配置
4. 根据需要查看各系统指南

---

## 🔗 快速导航

### 按功能查找

| 功能 | 文档 | 章节 |
|------|--------|------|
| 安装配置 | [主 README](../README.md#-快速开始) | 环境要求、安装步骤 |
| 用户管理 | [统一用户管理](./UNIFIED_SYSTEM_GUIDE.md) | 用户CRUD、权限控制 |
| Trilium 集成 | [知识库指南](./KB_SYSTEM_GUIDE.md#trilium-集成) | 笔记搜索、内容获取 |
| WebSocket 聊天 | [工单指南](./CASE_SYSTEM_GUIDE.md#websocket-实时聊天) | 实时通信 |
| 密码策略 | [安全文档](./SECURITY_IMPROVEMENTS.md#密码安全) | 密码强度验证 |

### 按问题查找

| 问题 | 文档 | 解决方案 |
|------|--------|----------|
| 数据库连接失败 | [主 README - 故障排除](../README.md#-故障排除) | 检查配置和服务 |
| Trilium 连接失败 | [主 README - 故障排除](../README.md#trilium-连接失败) | Token 生成和配置 |
| WebSocket 连接失败 | [主 README - 故障排除](../README.md#websocket-连接失败) | eventlet/gevent 安装 |
| 密码验证问题 | [安全文档](./SECURITY_IMPROVEMENTS.md#密码安全) | 密码策略配置 |

---

## 📝 文档更新记录

### 2026-02-12

#### 知识库管理优化
- ✅ 更新知识库管理功能说明
- ✅ 添加 Trilium 获取全部笔记方法文档
- ✅ 添加批量导入功能更新说明（支持 150 条）
- ✅ 添加管理界面修复记录

---

### 2026-02-10

#### 架构重构更新
- ✅ 更新所有文档，反映蓝图路由架构
- ✅ 添加新路由蓝图说明（`api_bp`, `auth_bp`）
- ✅ 更新 API 端点列表
- ✅ 更新项目结构图

#### 功能文档更新
- ✅ 添加 Trilium API 文档
- ✅ 添加密码复杂度说明
- ✅ 添加密码显示/隐藏功能说明

#### 安全文档更新
- ✅ 更新安全特性列表
- ✅ 添加审计日志说明

---

## 💡 使用提示

### 文档搜索技巧

1. **使用浏览器搜索**: `Ctrl+F` 或 `Cmd+F` 快速定位关键词
2. **查看目录**: 大多数文档都有清晰的目录结构
3. **代码示例**: 代码块标记为语言类型，支持语法高亮

### 在线资源

- [Swagger UI](http://localhost:5000/api/docs) - 交互式 API 文档
- [Flask 官方文档](https://flask.palletsprojects.com)
- [Trilium Notes](https://github.com/zadam/trilium-notes)

---

## 🤝 文档贡献

发现文档错误或有改进建议？

1. 直接提交 Pull Request 修改对应文档
2. 提交 Issue 说明需要改进的地方
3. 遵循 Markdown 格式规范

---

<div align="center">

**文档版本: v2.0.2** | 最后更新: 2026-02-12

</div>
