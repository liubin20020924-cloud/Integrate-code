# 官网系统开发指南

> 本指南专为修改官网前端内容设计，不涉及知识库和工单系统

## 📂 文件结构

```
官网系统文件：
├── routes/home_bp.py                    # 后端路由（你通常不需要修改）
├── templates/home/                      # ⭐ 主要修改这里
│   ├── index.html                       # 首页
│   ├── about.html                       # 关于我们
│   ├── cases.html                       # 客户案例
│   ├── parts.html                       # 备件库
│   ├── base.html                        # 基础模板
│   ├── admin_messages.html              # 留言管理
│   └── components/
│       ├── header.html                  # 导航栏
│       └── footer.html                  # 页脚
└── static/home/images/                  # ⭐ 图片资源
    ├── Logo1.jpg ~ Logo6.jpg            # Logo
    ├── 1.jpg ~ 5.jpg                    # 轮播图
    ├── BJ/                              # 背景图
    ├── ZZ/                              # 资质图标
    └── ZS/                              # 展示图标
```

## 🎯 常见修改任务

### 1. 修改首页标题和口号

**文件**: `templates/home/index.html`

**位置**: 第23-28行

```html
<h1 style="...">
    <span style="color: #A2D93D;">云户科技</span>
    <span>为企业IT保驾护航</span>
</h1>
<p style="...">
    "Make Customer Success, Enable Employee Growth"
</p>
```

### 2. 修改统计数据

**文件**: `templates/home/index.html`

**位置**: 第35-48行

```html
<div>
    <div>50+</div>
    <div>服务客户</div>
</div>
<div>
    <div>100%</div>
    <div>客户满意</div>
</div>
<div>
    <div>7×24</div>
    <div>技术支持</div>
</div>
```

### 3. 修改导航菜单

**文件**: `templates/home/components/header.html`

**查找**: `<nav>` 标签内的菜单项

```html
<a href="#home">首页</a>
<a href="#products">产品服务</a>
<a href="#cases">客户案例</a>
<a href="#about">关于我们</a>
```

### 4. 修改页脚信息

**文件**: `templates/home/components/footer.html`

**查找**: 公司信息、联系方式、社交媒体链接

### 5. 更换图片

#### 方法1: 直接替换文件
1. 将新图片命名为相同文件名（如 `Logo1.jpg`）
2. 放入 `static/home/images/` 目录
3. 刷新浏览器（可能需要清除缓存）

#### 方法2: 添加新图片
1. 上传新图片到 `static/home/images/`
2. 在模板中引用：
```html
<img src="/jpg/your-image.jpg" alt="描述">
```

### 6. 修改产品服务内容

**文件**: `templates/home/index.html`

**查找**: `<!-- 产品服务 -->` 注释附近的 `<section>` 标签

### 7. 修改客户案例

**文件**: `templates/home/cases.html`

**查找**: 案例卡片的 HTML 结构

### 8. 修改关于我们页面

**文件**: `templates/home/about.html`

**内容**: 公司介绍、团队展示、发展历程等

## 🎨 样式定制

### 品牌颜色

项目使用以下主色调：

```css
/* 主蓝色 */
#0A4DA2

/* 辅助绿色 */
#A2D93D

/* 文字颜色 */
#1a202c (深色)
#6b7280 (灰色)
#4b5563 (中灰)
```

### 修改全局样式

**文件**: `static/common.css`

这个文件包含所有页面的公共样式。

### 响应式设计

模板使用 `clamp()` 函数实现响应式：

```css
font-size: clamp(最小值, 理想值, 最大值);
/* 示例 */
font-size: clamp(1rem, 2vw, 1.5rem);
```

## 🖼️ 图片优化建议

当前存在的问题：
- ❌ 背景图过大（BJ1-BJ5，最大20MB）
- ❌ 未压缩的JPG文件

### 优化方法

#### 方法1: 使用脚本自动优化
```bash
python scripts/optimize_images.py
```

#### 方法2: 手动压缩
使用工具：
- [TinyPNG](https://tinypng.com/) - 在线压缩
- [ImageOptim](https://imageoptim.com/) - Mac应用
- Photoshop 的"存储为Web格式"

**建议设置**：
- 质量：80-85%
- 最大宽度：1920px（背景图）
- 最大宽度：800px（产品图）

## 📝 模板语法速查

### 继承模板
```html
{% extends "home/base.html" %}

{% block content %}
    你的内容
{% endblock %}
```

### 包含组件
```html
{% include 'home/components/header.html' %}
```

### 条件语句
```html
{% if user %}
    欢迎，{{ user.name }}
{% else %}
    请登录
{% endif %}
```

### 循环
```html
{% for item in items %}
    <div>{{ item.name }}</div>
{% endfor %}
```

### 访问配置
```html
{{ config.SITE_URL }}
```

## 🔗 路由参考

| URL | 页面 | 模板文件 |
|-----|------|---------|
| `/` | 首页 | `index.html` |
| `/about` | 关于我们 | `about.html` |
| `/cases` | 客户案例 | `cases.html` |
| `/parts` | 备件库 | `parts.html` |
| `/view-messages` | 留言管理 | `admin_messages.html` |

## 💾 联系表单API

**端点**: `POST /api/contact`

**请求格式**:
```json
{
    "name": "张三",
    "email": "test@example.com",
    "message": "留言内容"
}
```

**响应格式**:
```json
{
    "success": true,
    "message": "留言提交成功"
}
```

**前端调用示例**:
```javascript
fetch('/api/contact', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        name: '张三',
        email: 'test@example.com',
        message: '测试留言'
    })
})
.then(res => res.json())
.then(data => {
    if (data.success) {
        alert('提交成功！');
    }
});
```

## 🚀 本地开发流程

### 1. 启动应用
```bash
cd /Users/nutanix/Documents/GitHub/Integrate-code
.venv/bin/python app.py
```

### 2. 访问官网
打开浏览器访问：http://localhost:5001/

### 3. 修改文件
- 修改 HTML 模板
- 修改 CSS 样式
- 添加/替换图片

### 4. 刷新浏览器
- 按 `Cmd + Shift + R` (Mac) 强制刷新
- 清除浏览器缓存

### 5. 查看效果
- 检查页面显示
- 打开开发者工具 (F12) 查看错误

## 🐛 常见问题

### Q1: 修改后页面没有变化？

**A**: 清除浏览器缓存
```
Chrome: Cmd + Shift + R (Mac) / Ctrl + Shift + R (Windows)
```

### Q2: 图片显示404？

**A**: 检查以下几点：
1. 图片是否在 `static/home/images/` 目录
2. 文件名大小写是否正确
3. URL 是否使用 `/jpg/` 前缀

示例：
```html
✅ 正确：<img src="/jpg/Logo1.jpg">
❌ 错误：<img src="/static/home/images/Logo1.jpg">
❌ 错误：<img src="/jpg/logo1.jpg"> (大小写错误)
```

### Q3: 样式不生效？

**A**: 确保样式写在正确的位置：
1. 全局样式 → `static/common.css`
2. 页面内联样式 → 直接写在 `style` 属性
3. 清除浏览器缓存

### Q4: 如何添加新页面？

**步骤**：

1. 创建模板文件 `templates/home/newpage.html`
```html
{% extends "home/base.html" %}
{% block content %}
    {% include 'home/components/header.html' %}
    <h1>新页面</h1>
    {% include 'home/components/footer.html' %}
{% endblock %}
```

2. 在 `routes/home_bp.py` 添加路由
```python
@home_bp.route('/newpage')
def newpage():
    return render_template('home/newpage.html')
```

3. 重启应用，访问 http://localhost:5001/newpage

## 📚 推荐资源

### HTML/CSS 学习
- [MDN Web文档](https://developer.mozilla.org/zh-CN/)
- [W3Schools](https://www.w3schools.com/)
- [CSS-Tricks](https://css-tricks.com/)

### 设计灵感
- [Dribbble](https://dribbble.com/)
- [Awwwards](https://www.awwwards.com/)
- [Behance](https://www.behance.net/)

### 图标资源
- [Font Awesome](https://fontawesome.com/)
- [Heroicons](https://heroicons.com/)
- [Lucide](https://lucide.dev/)

### 图片素材
- [Unsplash](https://unsplash.com/)
- [Pexels](https://www.pexels.com/)
- [Pixabay](https://pixabay.com/)

## ⚠️ 注意事项

1. **不要修改知识库和工单系统**
   - ❌ 不要动 `templates/kb/`
   - ❌ 不要动 `templates/case/`
   - ❌ 不要动 `routes/kb_bp.py`
   - ❌ 不要动 `routes/case_bp.py`

2. **谨慎修改路由文件**
   - `routes/home_bp.py` 包含后端逻辑
   - 如需修改，请先备份

3. **图片命名规范**
   - 使用英文和数字
   - 避免空格和特殊字符
   - 使用小写字母（推荐）

4. **Git 协作**
   - 修改前先 `git pull`
   - 提交前先测试
   - 写清楚 commit 信息

5. **性能优化**
   - 压缩大图片
   - 避免使用超大背景图
   - 使用合适的图片格式（WebP > JPG > PNG）

## 🎓 快速上手示例

### 示例：修改首页标语

1. 打开文件：`templates/home/index.html`
2. 找到第27行左右
3. 修改文字：
```html
<p style="...">
    "您的新标语 Your New Slogan"
</p>
```
4. 保存文件
5. 刷新浏览器 (Cmd + Shift + R)

### 示例：添加新的统计数据

1. 打开文件：`templates/home/index.html`
2. 找到统计数据部分（第35-48行）
3. 复制一个 `<div>` 块：
```html
<div style="text-align: left;">
    <div style="font-size: clamp(1.5rem, 3vw, 2.25rem); font-weight: 800; color: #0A4DA2; line-height: 1;">10年</div>
    <div style="font-size: clamp(0.8rem, 0.9vw, 0.9rem); color: #6b7280; margin-top: 4px; font-weight: 500;">行业经验</div>
</div>
```
4. 保存并刷新

### 示例：更换Logo

1. 准备新Logo（建议尺寸：200x60px）
2. 命名为 `Logo1.jpg`
3. 复制到 `static/home/images/`
4. 如果模板已引用该文件，无需修改代码
5. 强制刷新浏览器

---

## 📞 需要帮助？

如果遇到问题：
1. 查看浏览器控制台（F12）的错误信息
2. 查看终端的错误日志
3. 向团队成员求助
4. 参考项目文档 `docs/HOME_SYSTEM_GUIDE.md`

---

**最后更新**: 2026-02-12  
**维护者**: AI开发助手
