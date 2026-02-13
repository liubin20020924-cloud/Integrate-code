# 云户科技网站 - 更新日志

> 记录项目的所有版本更新、功能改进、问题修复和优化记录

---

## 📋 版本索引

| 版本 | 日期 | 状态 |
|------|------|------|
| [v2.2](#v22-2026-02-13) | 2026-02-13 | 当前版本 |
| [v2.1](#v21-2026-02-12) | 2026-02-12 | 稳定版本 |
| [v2.0](#v20-2026-02-10) | 2026-02-10 | 架构重构 |

---

## v2.2 (2026-02-13)

### 🎯 主要更新

#### 1. Trilium 搜索功能修复 ⭐

**问题**: 知识库按内容搜索功能无法正常工作，显示"未找到匹配的笔记"

**修复内容**:
- ✅ 修复 JavaScript 语法错误（孤立 `.catch()` 代码块）
- ✅ 修复 API 数据结构不匹配（`data.data.count` → `results.length`）
- ✅ 添加安全的数据访问逻辑（防止访问 undefined 属性）
- ✅ 添加调试日志输出（便于问题排查）
- ✅ 防止事件监听器重复绑定（避免 429 错误）

**修改文件**:
- `templates/kb/index.html` - 删除孤立的 `.catch()` 块和测试代码
- `templates/kb/management.html` - 重写搜索函数，防止重复绑定

**详细记录**: [docs/KB_SEARCH_FIX.md](./KB_SEARCH_FIX.md)

---

#### 2. 文档结构优化 📚

**目标**: 统一管理项目文档，提升可维护性

**移动的文档**:
- `DATABASE_SETUP.md` → `docs/DATABASE_SETUP.md`
- `HOMEPAGE_DEV_GUIDE.md` → `docs/HOMEPAGE_DEV_GUIDE.md`
- `IMAGE_OPTIMIZATION_REPORT.md` → `docs/IMAGE_OPTIMIZATION_REPORT.md`
- `IMAGE_REPLACEMENT_COMPLETE.md` → `docs/IMAGE_REPLACEMENT_COMPLETE.md`
- `PROJECT_OPTIMIZATION_SUMMARY.md` → `docs/PROJECT_OPTIMIZATION_SUMMARY.md`

**新增文档**:
- `docs/KB_SEARCH_FIX.md` - Trilium 搜索功能修复记录

**更新文档**:
- `docs/README.md` - 更新文档索引和导航
- `docs/CHANGELOG.md` - 本文档，统一的更新日志

---

#### 3. 数据库改进 💾

**优化内容**:
- ✅ 添加数据库快速开始指南 (`database/QUICK_START.md`)
- ✅ 添加数据库 README (`database/README.md`)
- ✅ 整理数据库补丁脚本（按版本组织）
- ✅ 添加迁移脚本支持 v2.1 到 v2.2 版本升级

**新增文件**:
- `database/QUICK_START.md` - 快速开始指南
- `database/README.md` - 数据库文档索引
- `database/apply_patches_v2.1_to_v2.2.bat` - Windows 补丁脚本
- `database/apply_patches_v2.1_to_v2.2.sh` - Linux/Mac 补丁脚本
- `database/patches/v2.1_to_v2.2/` - v2.1 到 v2.2 的补丁文件

**重构文件**:
- `database/migrate_case_db.sql` → `database/patches/v2.1_to_v2.2/001_add_missing_columns.sql`
- `database/patch_kb_name_length.sql` → `database/patches/v2.1_to_v2.2/002_extend_kb_name_length.sql`

---

#### 4. 文案更新 ✏️

**修改内容**:
- ✅ "企业数字化转型" → "企业国产化转型" (5 处)
- ✅ "超融合维保" → "超融合虚拟化维保" (8 处)

**修改文件**:
- `templates/home/index.html` - 首页文案更新 (7 处)
- `templates/home/components/footer.html` - 页脚文案更新 (3 处)
- `templates/home/about.html` - 关于我们页面更新 (1 处)
- `templates/home/cases.html` - 用户案例页面更新 (2 处)

---

#### 5. 代码质量改进 🔧

**修改文件**:
- `common/trilium_helper.py` - Trilium 辅助函数优化
- `.gitignore` - 更新忽略规则，排除测试目录和临时文件

**新增文件**:
- `requirements-dev.txt` - 开发依赖文件

---

### 🐛 Bug 修复

| 问题 | 状态 | 详情 |
|------|------|------|
| JavaScript 语法错误 | ✅ 已修复 | 删除孤立代码块 |
| API 数据结构不匹配 | ✅ 已修复 | 修正数据访问逻辑 |
| 事件监听器重复绑定 | ✅ 已修复 | 添加防重复标志 |
| 429 错误 | ✅ 已修复 | 修复重复请求问题 |
| 自动 test 搜索 | ✅ 已修复 | 删除测试代码 |

---

### 📝 文档更新

**删除的文档**（从根目录移至 docs/）:
- `DATABASE_SETUP.md`
- `HOMEPAGE_DEV_GUIDE.md`
- `IMAGE_OPTIMIZATION_REPORT.md`
- `IMAGE_REPLACEMENT_COMPLETE.md`

**新增的文档**:
- `docs/KB_SEARCH_FIX.md`
- `docs/CHANGELOG.md`（本文档）

**更新的文档**:
- `docs/README.md`

---

### ⚠️ 重要提醒

1. **测试目录已排除** - `tests/` 目录已添加到 .gitignore
2. **文档已整理** - 原根目录的文档已移至 `docs/` 目录
3. **数据库补丁脚本** - 新版本提供了自动迁移脚本

---

## v2.1 (2026-02-12)

### 🎯 主要更新

#### 1. 图片优化完成 🖼️

**优化成果**:
- ✅ 压缩率达到 96.3%，节省 44.20 MB
- ✅ 超大图片 BJ2.jpg (20.73 MB → 140 KB)
- ✅ 生成 WebP 和 JPG 双格式
- ✅ 页面加载速度提升 90%+
- ✅ 每月可节省 $40 CDN 费用

**优化的页面**:
- 首页: ~3 MB → ~0.3 MB (节省 90%)
- 关于我们: ~2 MB → ~0.1 MB (节省 95%)
- 备件库: **41 MB** → **0.7 MB** (节省 98.3%) ⭐

**详细记录**:
- [docs/IMAGE_OPTIMIZATION_REPORT.md](./IMAGE_OPTIMIZATION_REPORT.md)
- [docs/IMAGE_REPLACEMENT_COMPLETE.md](./IMAGE_REPLACEMENT_COMPLETE.md)

---

#### 2. 知识库管理优化 📚

**更新内容**:
- ✅ 更新知识库管理功能说明
- ✅ 添加 Trilium 获取全部笔记方法文档
- ✅ 添加批量导入功能更新说明（支持 150 条）
- ✅ 添加管理界面修复记录

**修改文件**:
- `templates/kb/management.html` - 管理界面优化
- `docs/KB_MANAGEMENT_OPTIMIZATION.md` - 优化记录

---

#### 3. 官网首页优化 🎨

**优化内容**:
- ✅ 联系我们板块重新设计
- ✅ 渐变背景和装饰元素
- ✅ 联系方式卡片优化（悬停效果）
- ✅ 工作时间卡片优化（毛玻璃效果）
- ✅ 在线留言表单优化（聚焦效果）

**代码位置**: `templates/home/index.html` 第575-718行

---

### 📝 文档更新

**更新的文档**:
- `docs/HOMEPAGE_DEV_GUIDE.md` - 官网开发指南
- `docs/KB_MANAGEMENT_OPTIMIZATION.md` - 知识库管理优化
- `docs/PROJECT_OPTIMIZATION_SUMMARY.md` - 项目优化总结

---

## v2.0 (2026-02-10)

### 🎯 架构重构 ⭐

#### 1. 蓝图路由架构 🏗️

**重构内容**:
- ✅ 将统一路由文件 `routes_new.py` 拆分为蓝图架构
- ✅ 新增 `routes/__init__.py` - 蓝图注册
- ✅ 新增路由蓝图:
  - `home_bp.py` - 官网路由
  - `kb_bp.py` - 知识库认证和浏览路由
  - `kb_management_bp.py` - 知识库管理路由
  - `case_bp.py` - 工单系统路由
  - `unified_bp.py` - 统一用户管理路由
  - `auth_bp.py` - 认证 API 路由
  - `api_bp.py` - API 路由（Trilium 等）

**优势**:
- 模块化设计，易于维护
- 清晰的职责分离
- 便于团队协作
- 支持独立测试

---

#### 2. 统一用户管理 👥

**新增功能**:
- ✅ 统一的用户认证系统
- ✅ 基于角色的访问控制（RBAC）
- ✅ 用户管理界面（添加、编辑、删除用户）
- ✅ 密码复杂度验证（最少 6 位）
- ✅ 密码显示/隐藏功能
- ✅ 登录日志审计

**技术实现**:
- Werkzeug 密码加密（PBKDF2）
- Session 超时管理（3小时）
- 登录失败锁定

**详细文档**: [docs/UNIFIED_SYSTEM_GUIDE.md](./UNIFIED_SYSTEM_GUIDE.md)

---

#### 3. 安全改进 🔒

**新增安全特性**:
- ✅ 密码策略模块 (`common/password_policy.py`)
- ✅ 配置安全检查脚本
- ✅ 审计日志记录
- ✅ 输入验证器
- ✅ 统一 API 响应格式

**安全工具**:
- `scripts/check_config.py` - 配置安全检查
- `scripts/check_security.py` - 快速安全检查
- `scripts/generate_secure_env.py` - 生成安全配置

**详细文档**: [docs/SECURITY_IMPROVEMENTS.md](./SECURITY_IMPROVEMENTS.md)

---

#### 4. Trilium 集成优化 📝

**优化内容**:
- ✅ Trilium API 文档
- ✅ 笔记搜索功能
- ✅ 内容获取功能
- ✅ 附件代理支持
- ✅ 429 错误处理

**修复问题**:
- ✅ Trilium 429 错误（[docs/TRILIUM_429_FIX.md](./TRILIUM_429_FIX.md)）
- ✅ Trilium 公开访问配置（[docs/TRILIUM_PUBLIC_ACCESS_FIX.md](./TRILIUM_PUBLIC_ACCESS_FIX.md)）

**详细文档**: [docs/trilium-py-README.md](./trilium-py-README.md)

---

#### 5. 工单系统优化 🎫

**功能更新**:
- ✅ 移除自助注册功能
- ✅ 用户需由管理员创建
- ✅ WebSocket 实时聊天优化
- ✅ 工单状态管理
- ✅ 文件上传功能

**详细文档**: [docs/CASE_SYSTEM_GUIDE.md](./CASE_SYSTEM_GUIDE.md)

---

#### 6. 性能优化 ⚡

**优化内容**:
- ✅ 数据库连接池管理
- ✅ 结构化日志系统
- ✅ 响应式设计优化
- ✅ 图片懒加载

**代码统计**:
- 总代码量: ~24,000+ 行
- Python: ~8,000 行
- Templates: ~10,000 行
- CSS/JS: ~6,000 行

**详细文档**: [docs/CODE_STATISTICS.md](./CODE_STATISTICS.md)

---

### 📝 文档更新

**新增的文档**:
- `docs/HOME_SYSTEM_GUIDE.md` - 官网系统完整指南
- `docs/KB_SYSTEM_GUIDE.md` - 知识库系统完整指南
- `docs/CASE_SYSTEM_GUIDE.md` - 工单系统完整指南
- `docs/UNIFIED_SYSTEM_GUIDE.md` - 统一用户管理完整指南
- `docs/API_DOCS.md` - RESTful API 文档
- `docs/SECURITY_IMPROVEMENTS.md` - 安全特性说明
- `docs/TRILIUM_429_FIX.md` - 429 错误修复
- `docs/TRILIUM_PUBLIC_ACCESS_FIX.md` - 公开访问修复
- `docs/TRILIUM_QUICK_ADD.md` - Trilium 快速添加
- `docs/CONFIGURATION_GUIDE.md` - 配置指南

**更新的文档**:
- `docs/README.md` - 文档索引
- `docs/OPTIMIZATION_PLAN.md` - 优化计划
- `docs/CODE_STATISTICS.md` - 代码统计

---

## 📊 版本对比

### 功能对比

| 功能 | v1.x | v2.0 | v2.1 | v2.2 |
|------|------|------|------|------|
| 官网系统 | ✅ | ✅ | ✅ | ✅ |
| 知识库系统 | ✅ | ✅ | ✅ | ✅ |
| 工单系统 | ✅ | ✅ | ✅ | ✅ |
| 统一用户管理 | ❌ | ✅ | ✅ | ✅ |
| 蓝图路由架构 | ❌ | ✅ | ✅ | ✅ |
| Trilium 搜索 | ⚠️ | ✅ | ✅ | ✅ 修复 |
| 图片优化 | ❌ | ❌ | ✅ | ✅ |
| 文档结构 | ❌ | ❌ | ⚠️ | ✅ |
| 429 错误处理 | ❌ | ⚠️ | ⚠️ | ✅ 修复 |

### 性能对比

| 指标 | v1.x | v2.0 | v2.1 | v2.2 |
|------|------|------|------|------|
| 首页加载时间 | ~5秒 | ~4秒 | ~0.5秒 | ~0.5秒 |
| 图片总大小 | 45.9 MB | 45.9 MB | 1.7 MB | 1.7 MB |
| 代码行数 | ~15,000 | ~24,000 | ~24,000 | ~24,000 |
| 文档数量 | 5 | 15 | 20 | 15* |

*注: v2.2 合并了部分文档

---

## 🚀 升级指南

### 从 v2.1 升级到 v2.2

1. **拉取最新代码**
```bash
git pull origin 2.1
```

2. **安装开发依赖**（如需要）
```bash
pip install -r requirements-dev.txt
```

3. **应用数据库补丁**（如果使用数据库）
```bash
# Windows
database/apply_patches_v2.1_to_v2.2.bat

# Linux/Mac
bash database/apply_patches_v2.1_to_v2.2.sh
```

4. **重启应用**
```bash
# Windows
start.bat

# Linux/Mac
bash start.sh
```

5. **验证功能**
- 访问知识库页面
- 测试内容搜索功能
- 检查搜索结果是否正常显示

---

### 从 v2.0 升级到 v2.1

1. **拉取最新代码**
```bash
git pull origin main
```

2. **验证图片优化**
```bash
# 检查优化后的图片是否存在
ls static/home/images/optimized/
ls static/home/images/BJ/optimized/
```

3. **重启应用**
```bash
python app.py
```

4. **测试页面加载**
- 访问首页: http://localhost:5001/
- 检查 Network 面板的图片加载大小
- 确认 WebP 格式被使用

---

### 从 v1.x 升级到 v2.0

⚠️ **重大架构变更，需要仔细规划**

1. **备份数据库**
```bash
# 备份所有数据库
mariadb-dump clouddoors_db > clouddoors_db_backup.sql
mariadb-dump YHKB > YHKB_backup.sql
mariadb-dump casedb > casedb_backup.sql
```

2. **拉取新代码**
```bash
git fetch origin
git checkout v2.0
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **更新配置文件**
```bash
# 参考 .env.example 更新 .env
cp .env.example .env
# 编辑 .env 文件
```

5. **运行迁移脚本**
```bash
bash init_db.sh
```

6. **重启应用**
```bash
python app.py
```

7. **验证功能**
- 测试所有系统功能
- 验证用户登录
- 检查数据库连接

---

## 📚 相关文档

### 系统指南
- [官网系统指南](./HOME_SYSTEM_GUIDE.md)
- [知识库系统指南](./KB_SYSTEM_GUIDE.md)
- [工单系统指南](./CASE_SYSTEM_GUIDE.md)
- [统一用户管理指南](./UNIFIED_SYSTEM_GUIDE.md)

### API 文档
- [API 文档](./API_DOCS.md)
- [Trilium 集成](./trilium-py-README.md)

### 开发指南
- [官网开发指南](./HOMEPAGE_DEV_GUIDE.md)
- [数据库设置](./DATABASE_SETUP.md)
- [项目优化总结](./PROJECT_OPTIMIZATION_SUMMARY.md)

### 问题修复记录
- [Trilium 429 错误修复](./TRILIUM_429_FIX.md)
- [Trilium 公开访问修复](./TRILIUM_PUBLIC_ACCESS_FIX.md)
- [知识库搜索修复](./KB_SEARCH_FIX.md)

### 安全与优化
- [安全改进文档](./SECURITY_IMPROVEMENTS.md)
- [优化计划](./OPTIMIZATION_PLAN.md)
- [代码统计](./CODE_STATISTICS.md)

---

## 🤝 贡献者

感谢所有为项目做出贡献的开发者！

- AI 开发助手 - 架构设计、功能实现、文档编写

---

## 📞 获取帮助

如果遇到问题：

1. 查看本文档的相关章节
2. 阅读对应的系统指南
3. 查看问题修复记录
4. 提交 Issue 说明问题

---

**文档版本**: v1.0
**最后更新**: 2026-02-13
**维护者**: Claude AI Assistant
