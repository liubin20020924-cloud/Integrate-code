# 云户科技网站 - Python Flask 版本

这是云户科技网站的Python Flask重写版本，将原PHP项目转换为Python项目。

## 功能特点

- ✅ 完整保留原有页面显示样式
- ✅ 将首页拆分为独立组件（header、home、about、services、cases、solutions、contact、footer）
- ✅ 保留所有弹窗显示功能
- ✅ 保留所有状态和交互功能
- ✅ 保留数据库功能（MySQL）
- ✅ 表单提交使用AJAX
- ✅ 留言管理后台
- ✅ 支持搜索和分页

## 安装步骤

### 1. 确保已安装Python 3.7+

```bash
python --version
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置数据库

编辑 `.env` 文件，配置数据库连接信息：

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=clouddoors_db
DB_PORT=3306
SECRET_KEY=your-secret-key-change-this-in-production
```

### 4. 初始化数据库

运行初始化脚本创建数据库表：

```bash
python init_db.py
```

### 5. 启动应用

```bash
python app.py
```

访问地址: http://localhost:5000

## 项目结构

```
cloud-doors/
├── app.py                  # Flask应用入口
├── config.py               # 配置文件
├── models.py               # 数据库模型
├── validators.py           # 表单验证
├── init_db.py              # 数据库初始化脚本
├── requirements.txt        # Python依赖
├── .env                    # 环境变量配置
├── jpg/                    # 图片文件夹
├── routes/
│   ├── __init__.py
│   ├── main.py             # 主路由
│   ├── api.py              # API路由
│   └── admin.py            # 管理后台路由
└── templates/
    ├── base.html           # 基础模板
    ├── index.html          # 首页
    ├── view_messages.html  # 留言管理页面
    └── components/
        ├── header.html     # 导航栏组件
        ├── home.html       # 首页内容组件
        ├── about.html      # 专业服务组件
        ├── services.html   # 业务介绍组件
        ├── cases.html      # 用户案例组件
        ├── solutions.html  # 解决方案组件
        ├── contact.html    # 联系我们组件
        └── footer.html     # 页脚组件
```

## 页面组件说明

1. **header.html** - 导航栏，包含Logo、导航菜单、移动端菜单
2. **home.html** - 首页横幅，展示公司简介和CTA按钮
3. **about.html** - 专业服务部分，包含备品备件、实验环境、知识库三个标签页
4. **services.html** - 业务介绍，展示9个核心业务卡片
5. **cases.html** - 用户案例，展示3个客户案例
6. **solutions.html** - 解决方案，展示4个解决方案
7. **contact.html** - 联系我们，包含联系表单和联系方式
8. **footer.html** - 页脚，包含快速链接、业务范围、联系方式

## API接口

### 提交表单
- URL: `/api/submit-form`
- Method: `POST`
- 参数: `name`, `phone`, `email`, `message`

### 获取留言列表
- URL: `/api/messages`
- Method: `GET`
- 参数: `search` (可选), `page` (可选, 默认1)

### 获取单条留言
- URL: `/api/messages/<id>`
- Method: `GET`

### 删除留言
- URL: `/api/messages/<id>`
- Method: `DELETE`

### 更新留言状态
- URL: `/api/messages/<id>/status`
- Method: `PUT`
- 参数: `status` (1:未处理, 2:已联系, 3:已完成)

## 管理后台

访问 `/admin/messages` 可以查看和管理留言列表。

## 数据库

使用MySQL数据库，表结构：

```sql
CREATE TABLE contact_messages (
  id INT(11) NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  email VARCHAR(100) DEFAULT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status TINYINT(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

## 注意事项

1. 确保 `jpg` 文件夹存在且包含所有必要的图片文件
2. 数据库连接信息需要正确配置
3. 建议在生产环境中使用更安全的SECRET_KEY
4. 生产环境建议使用Nginx或Apache作为反向代理

## 开发环境

- Python 3.7+
- Flask 3.0.0
- MySQL 5.7+
