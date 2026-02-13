# 云户科技网站 - 文档中心

> 项目文档索引和快速导航指南

---

## 📚 文档列表

### 快速开始

| 文档 | 说明 | 适用场景 |
|--------|------|----------|
| [更新日志](./CHANGELOG.md) | 版本更新历史、功能改进、问题修复 | 了解最新功能 |
| [数据库快速开始](../database/QUICK_START.md) | 数据库初始化和配置 | 环境搭建 |

### 系统指南

| 文档 | 说明 | 目标读者 |
|--------|------|----------|
| [官网系统指南](./HOME_SYSTEM_GUIDE.md) | 官网系统功能说明和使用 | 所有用户 |
| [知识库系统指南](./KB_SYSTEM_GUIDE.md) | 知识库浏览、搜索、管理 | 知识库用户 |
| [工单系统指南](./CASE_SYSTEM_GUIDE.md) | 工单创建、聊天、跟踪 | 客户/服务人员 |
| [统一用户管理指南](./UNIFIED_SYSTEM_GUIDE.md) | 用户管理、权限控制 | 管理员 |

### API 文档

| 文档 | 说明 | 目标读者 |
|--------|------|----------|
| [API 文档](./API_DOCS.md) | RESTful API 接口说明 | 开发者 |
| [Trilium 集成](./trilium-py-README.md) | Trilium 笔记服务集成 | 知识库开发者 |

### 开发指南

| 文档 | 说明 | 目标读者 |
|--------|------|----------|
| [官网开发指南](./HOMEPAGE_DEV_GUIDE.md) | 官网前端开发修改指南 | 前端开发者 |
| [数据库设置](./DATABASE_SETUP.md) | 数据库初始化和配置 | 开发者/运维 |
| [项目优化总结](./PROJECT_OPTIMIZATION_SUMMARY.md) | 项目架构和优化记录 | 开发者 |
| [配置指南](./CONFIGURATION_GUIDE.md) | 系统配置详细说明 | 开发者/运维 |

### 安全与优化

| 文档 | 说明 | 适用场景 |
|--------|------|----------|
| [优化建议](./OPTIMIZATION_RECOMMENDATIONS.md) | 全面的代码分析和优化建议 | 开发者/运维 |
| [安全改进文档](./SECURITY_IMPROVEMENTS.md) | 安全特性和最佳实践 | 安全审计 |
| [优化计划](./OPTIMIZATION_PLAN.md) | 历史优化记录（已过时） | 参考 |
| [代码统计](./CODE_STATISTICS.md) | 代码量和技术栈分析 | 项目评估 |
| [知识库管理优化](./KB_MANAGEMENT_OPTIMIZATION.md) | 知识库管理功能更新和修复 | 知识库开发者 |

### 问题修复记录

| 文档 | 说明 | 适用场景 |
|--------|------|----------|
| [Trilium 429 错误修复](./TRILIUM_429_FIX.md) | API 限流问题修复 | 开发者 |
| [Trilium 公开访问修复](./TRILIUM_PUBLIC_ACCESS_FIX.md) | 公开访问配置问题修复 | 开发者 |
| [知识库搜索修复](./KB_SEARCH_FIX.md) | Trilium 搜索功能修复 | 开发者 |

### Trilium 相关文档

| 文档 | 说明 | 目标读者 |
|--------|------|----------|
| [Trilium 快速添加](./TRILIUM_QUICK_ADD.md) | 快速添加 Trilium 笔记 | 知识库管理员 |
| [Trilium 搜索指南](./TRILIUM_SEARCH_GUIDE.md) | Trilium 搜索功能说明 | 知识库用户 |

### 图片优化记录

| 文档 | 说明 | 适用场景 |
|--------|------|----------|
| [图片优化报告](./IMAGE_OPTIMIZATION_REPORT.md) | 图片压缩和优化详情 | 性能优化 |
| [图片替换完成](./IMAGE_REPLACEMENT_COMPLETE.md) | 图片优化部署记录 | 前端开发 |

---

## 🗂 文档结构

```
docs/
├── README.md                              # 本文件 - 文档索引
├── CHANGELOG.md                           # 更新日志（主要）
│
├── 快速开始和安装
│   ├── DATABASE_SETUP.md                   # 数据库初始化指南
│   └── database/
│       ├── QUICK_START.md                  # 数据库快速开始
│       └── README.md                      # 数据库文档索引
│
├── 系统指南
│   ├── HOME_SYSTEM_GUIDE.md                # 官网系统完整指南
│   ├── KB_SYSTEM_GUIDE.md                  # 知识库系统完整指南
│   ├── CASE_SYSTEM_GUIDE.md                # 工单系统完整指南
│   └── UNIFIED_SYSTEM_GUIDE.md            # 统一用户管理完整指南
│
├── API 文档
│   ├── API_DOCS.md                        # RESTful API 文档
│   └── trilium-py-README.md               # Trilium 集成文档
│
├── 开发指南
│   ├── HOMEPAGE_DEV_GUIDE.md              # 官网前端开发指南
│   ├── PROJECT_OPTIMIZATION_SUMMARY.md    # 项目优化总结
│   ├── KB_MANAGEMENT_OPTIMIZATION.md      # 知识库管理优化
│   └── CONFIGURATION_GUIDE.md             # 配置指南
│
├── 安全与优化
│   ├── SECURITY_IMPROVEMENTS.md            # 安全特性说明
│   ├── OPTIMIZATION_PLAN.md               # 优化计划文档
│   └── CODE_STATISTICS.md                 # 代码统计信息
│
├── 问题修复记录
│   ├── TRILIUM_429_FIX.md                 # 429 错误修复
│   ├── TRILIUM_PUBLIC_ACCESS_FIX.md       # 公开访问修复
│   └── KB_SEARCH_FIX.md                   # 知识库搜索修复
│
└── Trilium 相关文档
    ├── TRILIUM_QUICK_ADD.md               # Trilium 快速添加
    └── TRILIUM_SEARCH_GUIDE.md           # Trilium 搜索指南
```

---

## 📖 文档阅读顺序

### 新用户

1. 阅读 [更新日志](./CHANGELOG.md) 了解最新版本
2. 根据 [数据库快速开始](../database/QUICK_START.md) 完成数据库初始化
3. 阅读 [系统指南](#-系统指南) 了解对应系统功能
4. 参考 [安全改进文档](./SECURITY_IMPROVEMENTS.md) 配置生产环境

### 开发者

1. 阅读 [更新日志](./CHANGELOG.md) 了解版本历史
2. 查阅 [API 文档](./API_DOCS.md) 了解接口规范
3. 参考 [优化计划](./OPTIMIZATION_PLAN.md) 了解架构设计
4. 查看 [代码统计](./CODE_STATISTICS.md) 了解技术栈

### 管理员

1. 阅读 [更新日志](./CHANGELOG.md) 了解新功能
2. 查看 [统一用户管理指南](./UNIFIED_SYSTEM_GUIDE.md) 学习用户管理
3. 参考 [安全改进文档](./SECURITY_IMPROVEMENTS.md) 了解安全配置
4. 根据需要查看各系统指南

### 前端开发者

1. 阅读 [官网开发指南](./HOMEPAGE_DEV_GUIDE.md) 了解前端结构
2. 参考 [官网系统指南](./HOME_SYSTEM_GUIDE.md) 了解功能说明
3. 查看模板文件 `templates/home/`
4. 查看样式文件 `static/common.css`

---

## 🔗 快速导航

### 按功能查找

| 功能 | 文档 | 章节 |
|------|--------|------|
| 版本更新 | [CHANGELOG.md](./CHANGELOG.md) | 所有版本记录 |
| 数据库配置 | [数据库快速开始](../database/QUICK_START.md) | 数据库初始化 |
| 用户管理 | [统一用户管理](./UNIFIED_SYSTEM_GUIDE.md) | 用户CRUD、权限控制 |
| Trilium 集成 | [知识库指南](./KB_SYSTEM_GUIDE.md#trilium-集成) | 笔记搜索、内容获取 |
| WebSocket 聊天 | [工单指南](./CASE_SYSTEM_GUIDE.md#websocket-实时聊天) | 实时通信 |
| 密码策略 | [安全文档](./SECURITY_IMPROVEMENTS.md#密码安全) | 密码强度验证 |
| 前端修改 | [官网开发指南](./HOMEPAGE_DEV_GUIDE.md) | HTML/CSS 修改 |

### 按问题查找

| 问题 | 文档 | 解决方案 |
|------|--------|----------|
| 数据库连接失败 | [DATABASE_SETUP.md](./DATABASE_SETUP.md#故障排除) | 检查配置和服务 |
| Trilium 连接失败 | [TRILIUM_PUBLIC_ACCESS_FIX.md](./TRILIUM_PUBLIC_ACCESS_FIX.md) | Token 生成和配置 |
| 429 错误 | [TRILIUM_429_FIX.md](./TRILIUM_429_FIX.md) | API 限流处理 |
| 搜索功能异常 | [KB_SEARCH_FIX.md](./KB_SEARCH_FIX.md) | 搜索功能修复 |
| 密码验证问题 | [安全文档](./SECURITY_IMPROVEMENTS.md#密码安全) | 密码策略配置 |

---

## 📝 文档更新记录

### 2026-02-13

#### 文档结构重组
- ✅ 创建统一的 [CHANGELOG.md](./CHANGELOG.md)
- ✅ 删除冗余和过时的文档
- ✅ 更新文档索引和导航

#### 删除的文档
- `CASE_SYSTEM_COMPLETION.md` - 已合并到工单系统指南
- `CONFIG_OPTIMIZATION_SUMMARY.md` - 已合并到优化计划
- `IMAGE_LOADING_OPTIMIZATION_PLAN.md` - 已合并到图片优化报告
- `IMAGE_OPTIMIZATION_GUIDE.md` - 已合并到图片优化报告
- `MD_SECURITY_CLEANUP_REPORT.md` - 已合并到安全改进文档
- `NGINX_CONFIG_COMPARISON.md` - 过时的配置对比
- `NGINX_UPGRADE_GUIDE.md` - 过时的升级指南
- `QUICK_OPTIMIZE_REFERENCE.md` - 已合并到优化计划
- `nginx_*.conf` - 示例配置文件
- `SYSTEM_UPDATE_NOTES.md` - 已合并到 CHANGELOG.md

---

### 2026-02-12

#### 图片优化完成
- ✅ 更新 [IMAGE_OPTIMIZATION_REPORT.md](./IMAGE_OPTIMIZATION_REPORT.md)
- ✅ 更新 [IMAGE_REPLACEMENT_COMPLETE.md](./IMAGE_REPLACEMENT_COMPLETE.md)
- ✅ 图片压缩率达到 96.3%
- ✅ 页面加载速度提升 90%+

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

**文档版本: v2.1** | 最后更新: 2026-02-13

</div>
