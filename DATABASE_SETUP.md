# MariaDB 数据库初始化指南

## 初始化步骤

### 1. 运行初始化脚本

```bash
./init_db.sh
```

或者手动执行：

```bash
sudo mariadb < database/init_database.sql
```

### 2. 验证数据库

```bash
sudo mariadb -e "SHOW DATABASES;"
```

应该看到以下数据库：
- `clouddoors_db` - 官网系统
- `YHKB` - 知识库系统  
- `casedb` - 工单系统

### 3. 启动应用

```bash
.venv/bin/python app.py
```

## 默认账号

- **用户名**: `admin`
- **密码**: `YHKB@2024`

⚠️ **重要**: 生产环境请立即修改默认密码！

## 数据库连接说明

MariaDB 默认配置下，root 用户使用 unix_socket 认证。如果需要密码认证，请执行：

```bash
sudo mariadb
```

然后在 MariaDB 中执行：

```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_password';
FLUSH PRIVILEGES;
EXIT;
```

然后更新 `.env` 文件中的 `DB_PASSWORD`。

## 故障排除

如果遇到连接错误，请确认：
1. MariaDB 服务已启动：`brew services list`
2. 数据库已创建：`sudo mariadb -e "SHOW DATABASES;"`
3. `.env` 文件配置正确
