# 云户科技网站 - 整合项目

整合官网、知识库、工单三个系统的统一项目。

> 📚 **文档目录**: 所有项目文档已移至 [`./docs/`](./docs/) 目录，请查看该目录获取详细文档。

## 项目结构

```
Integrate-code/
├── app.py                    # 主入口文件
├── config.py                 # 统一配置文件
├── requirements.txt          # 依赖文件
├── init_database.sql         # 数据库初始化脚本
├── modules/                  # 模块目录
│   ├── case/                # 工单系统模块
│   │   ├── routes.py       # 工单路由
│   │   └── __init__.py
│   ├── kb/                  # 知识库系统模块
│   │   ├── app.py          # 知识库应用
│   │   ├── auth/           # 认证模块
│   │   ├── database/       # 数据库模块
│   │   ├── management/     # 管理模块
│   │   ├── views/          # 视图模块
│   │   └── __init__.py
│   ├── home/                # 官网系统模块
│   │   ├── app.py          # 官网应用
│   │   ├── routes/         # 路由模块
│   │   └── __init__.py
│   └── unified/             # 统一用户管理模块
│       ├── routes.py       # 用户管理路由
│       ├── utils.py        # 工具函数
│       └── __init__.py
├── static/                  # 静态文件
│   ├── case/               # 工单系统前端
│   ├── kb/                 # 知识库静态资源
│   └── home/               # 官网静态资源
├── templates/               # 模板文件
│   ├── kb/                 # 知识库模板
│   ├── home/               # 官网模板
│   └── unified/            # 统一用户管理模板
├── common/                  # 公共模块
│   └── db_manager.py       # 数据库连接管理
├── instance/                # SQLite数据库文件（官网）
└── docs/                    # 文档目录
```

## 快速启动

### 1. 安装依赖

```bash
# 安装依赖
pip install -r requirements.txt
```

或直接运行启动脚本（会自动创建虚拟环境）：

```bash
run.bat
```

### 2. 配置数据库

编辑 `config.py` 文件，配置数据库连接信息：

```python
# 通用数据库配置（三个系统共用）
DB_HOST = '10.10.10.254'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = 'Nutanix/4u123!'

# 各系统数据库名称
DB_NAME_HOME = 'clouddoors_db'  # 官网系统数据库
DB_NAME_KB = 'YHKB'              # 知识库系统数据库
DB_NAME_CASE = 'casedb'           # 工单系统数据库
```

### 3. 启动服务

```bash
python app.py
```

或使用启动脚本：

```bash
run.bat
```

## 访问地址

启动成功后，可以通过以下地址访问各系统：

- **官网首页**: http://localhost:5000/
- **知识库系统**: http://localhost:5000/kb
- **工单系统**: http://localhost:5000/case
- **统一用户管理**: http://localhost:5000/unified/users

## 系统说明

### 官网系统

- **功能**: 公司官网展示、产品介绍、解决方案等
- **数据库**: MySQL (clouddoors_db) 或 SQLite (instance/clouddoors.db)
- **特点**: 静态展示为主，包含联系表单等交互功能

### 知识库系统

- **功能**: 知识文档管理、搜索、内容查看
- **数据库**: MySQL (YHKB)
- **特点**: 集成Trilium笔记系统，支持用户认证和权限管理
- **默认管理员**: admin / YHKB@2024

### 工单系统

- **功能**: 工单提交、处理、实时聊天、邮件通知
- **数据库**: MySQL (casedb)
- **特点**: 支持WebSocket实时通信，客户可创建工单并实时交流
- **默认管理员**: admin / admin123

## 配置说明

### 环境变量配置

可以使用 `.env` 文件配置敏感信息：

```env
SECRET_KEY=your-secret-key
DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# 数据库配置
DB_HOST=10.10.10.254
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password

# 各系统数据库名称
DB_NAME_HOME=clouddoors_db
DB_NAME_KB=YHKB
DB_NAME_CASE=casedb

# Trilium配置
TRILIUM_SERVER_URL=http://10.10.10.254:8080
TRILIUM_TOKEN=your-token

# 邮件配置
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=your-email@qq.com
SMTP_PASSWORD=your-password
```

### 数据库初始化

项目首次运行时，会自动创建所需的数据库表：

1. **工单系统**: 创建 tickets, messages, users 表
2. **知识库系统**: 创建 mgmt_users, mgmt_login_logs 表（如果不存在）
3. **官网系统**: 使用SQLite数据库（自动创建）

## 依赖说明

主要依赖包：

- **Flask**: Web框架
- **Flask-SQLAlchemy**: ORM工具
- **Flask-SocketIO**: WebSocket支持
- **PyMySQL**: MySQL驱动
- **python-dotenv**: 环境变量管理
- **trilium-py**: Trilium API客户端

详细依赖列表见 `requirements.txt`。

## 注意事项

1. **数据库配置**: 请确保各系统的数据库已创建并配置正确的连接信息
2. **端口冲突**: 默认使用5000端口，如需修改请在config.py中更改FLASK_PORT
3. **生产环境**: 生产环境部署时请设置DEBUG=False，并修改SECRET_KEY
4. **文件权限**: 确保static和templates目录有正确的读写权限

## 故障排除

### 数据库连接失败

检查数据库服务是否启动，配置是否正确：

```bash
# 测试MySQL连接
mysql -h 127.0.0.1 -u root -p
```

### 模块导入错误

确保在项目根目录运行，并且Python版本在3.8+：

```bash
python --version
```

### 端口被占用

修改config.py中的FLASK_PORT为其他端口：

```python
FLASK_PORT = 5001
```

## 技术支持

如有问题请联系技术支持。
