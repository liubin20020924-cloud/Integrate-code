# Trilium 快速添加功能说明

## 功能概述

知识库管理系统现在集成了 Trilium 笔记库的快速搜索和导入功能，让您可以快速从 Trilium 中查找笔记并添加到知识库中。

## 主要功能

### 1. 从 Trilium 搜索笔记

**入口位置：**
- 知识库管理页面 → 添加记录 → 知识库名称输入框旁的"从 Trilium 搜索"按钮

**使用步骤：**

1. 打开添加记录模态框
2. 在"知识库名称"输入框旁边，点击"从 Trilium 搜索"按钮
3. 在弹出的搜索框中输入关键词（支持标题、内容搜索）
4. 点击搜索或按回车键
5. 在搜索结果中点击笔记即可选中

**功能特点：**
- 实时搜索 Trilium 笔记库
- 显示笔记标题、ID、类型和修改时间
- 点击笔记即可自动填充到表单
- 支持最多返回 20 条结果

### 2. 预览 Trilium 笔记

**入口位置：**
- 添加记录模态框 → Trilium 链接输入框旁的"预览"按钮

**使用步骤：**

1. 在"Trilium 链接"输入框中粘贴笔记链接
   - 格式：`http://trilium.example.com/#root/笔记ID`
2. 点击"预览"按钮
3. 查看笔记的详细信息（标题、ID、类型）
4. 点击"使用此笔记"按钮将信息填充到表单

**功能特点：**
- 显示笔记基本信息
- 自动填充知识库名称
- 自动生成 Trilium 链接

### 3. 批量添加（已有功能）

**格式说明：**
```
编号,名称,链接
1001,常见问题,https://trilium.example.com/#root/abc
1002,系统配置,https://trilium.example.com/#root/def
```

**快捷操作：**
- 支持从 Excel 复制数据后直接粘贴
- 每行一条记录，使用逗号分隔

## API 接口

### 1. 搜索 Trilium 笔记

```
GET /kb/MGMT/api/trilium/search
```

**参数：**
- `query` (必填): 搜索关键词
- `limit` (可选): 返回结果数量限制，默认 20

**响应示例：**
```json
{
  "success": true,
  "message": "搜索成功",
  "data": {
    "results": [
      {
        "noteId": "ABC123",
        "title": "常见问题",
        "type": "text",
        "dateModified": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

### 2. 获取 Trilium 笔记详情

```
GET /kb/MGMT/api/trilium/note
```

**参数：**
- `note_id` (必填): 笔记 ID

**响应示例：**
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "note": {
      "noteId": "ABC123",
      "title": "常见问题",
      "content": "<p>笔记内容...</p>",
      "type": "text",
      "dateModified": "2024-01-15T10:30:00Z"
    }
  }
}
```

## 配置要求

确保 `.env` 文件中已正确配置 Trilium 连接信息：

```env
# Trilium 服务器地址
TRILIUM_SERVER_URL=http://trilium.example.com:8080

# Trilium ETAPI Token（必须）
TRILIUM_TOKEN=your-token-here

# Trilium 登录密码（可选，如果没有token）
TRILIUM_LOGIN_USERNAME=
TRILIUM_LOGIN_PASSWORD=
```

**获取 ETAPI Token 的方法：**
1. 打开 Trilium
2. 进入 Options → ET API
3. 点击 "Generate Token" 生成新的令牌
4. 复制 Token 到 `.env` 文件的 `TRILIUM_TOKEN` 配置项

## 工作流程

### 快速添加流程

1. **登录知识库管理系统**
   - 访问 `/kb/MGMT`
   - 使用管理员账号登录

2. **打开添加记录**
   - 点击"添加记录"按钮

3. **从 Trilium 搜索**
   - 点击"从 Trilium 搜索"
   - 输入关键词搜索
   - 点击选中的笔记

4. **填写知识库编号**
   - 手动输入知识库编号（必填）
   - 知识库名称已自动填充
   - Trilium 链接已自动生成

5. **保存记录**
   - 点击"保存"按钮
   - 系统会验证并保存到数据库

### 手动填写流程

1. 打开添加记录
2. 手动填写：
   - 知识库编号（必填，数字）
   - 知识库名称（必填，文本）
   - Trilium 链接（可选，URL 格式）
3. 点击"预览"按钮查看笔记信息（可选）
4. 点击"保存"

## 优势说明

### 1. 提高效率
- 无需手动复制粘贴
- 搜索和选择笔记一步完成
- 自动填充表单字段

### 2. 减少错误
- 自动生成正确的笔记链接
- 避免手动输入错误
- 提供预览功能确认信息

### 3. 统一管理
- 知识库与 Trilium 集成
- 便于后续维护和更新
- 保持数据一致性

## 常见问题

### Q: 搜索不到笔记？
**A:** 请检查：
1. Trilium 服务是否正常运行
2. `.env` 文件中的 `TRILIUM_TOKEN` 是否正确
3. Trilium 服务器地址是否配置正确

### Q: 点击笔记后表单没有填充？
**A:** 请检查：
1. 笔记是否有标题
2. 浏览器控制台是否有错误
3. 刷新页面后重试

### Q: 预览功能不工作？
**A:** 可能原因：
1. 笔记 ID 格式不正确
2. Token 权限不足
3. 笔记不存在或已删除

### Q: 如何批量导入已有数据？
**A:**
1. 准备 CSV 格式数据：`编号,名称,链接`
2. 点击"批量添加"按钮
3. 粘贴数据并点击"添加"

## 技术实现

### 后端实现
- 使用 `trilium-py` 库调用 Trilium ETAPI
- 在 `kb_management_bp.py` 中添加了两个新接口：
  - `/api/trilium/search` - 搜索笔记
  - `/api/trilium/note` - 获取笔记详情
- 利用现有的 `TriliumHelper` 类处理 API 调用

### 前端实现
- 添加 Trilium 搜索模态框
- 实时搜索结果显示
- 笔记预览功能
- 自动填充表单字段

## 后续优化建议

1. **批量导入 Trilium 笔记**
   - 支持一次性从 Trilium 导入多个笔记
   - 自动生成知识库编号

2. **双向同步**
   - 知识库记录变更时同步到 Trilium
   - Trilium 笔记变更时更新知识库

3. **高级搜索**
   - 支持按笔记类型筛选
   - 支持按时间范围搜索
   - 支持标签搜索

4. **快速创建**
   - 从 Trilium 笔记创建时直接添加到知识库
   - 无需在两个系统间切换

## 更新日志

### 2026-02-12
- ✨ 新增 Trilium 笔记搜索功能
- ✨ 新增 Trilium 笔记预览功能
- ✨ 优化添加记录的用户体验
- 🐛 修复 CSRF 保护导致的登录问题
