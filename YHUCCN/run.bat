@echo off
echo ====================================
echo 云户科技网站启动脚本
echo ====================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo 1. 检查依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo 警告: 依赖安装可能存在问题，继续启动...
)
echo.

echo 2. 初始化数据库...
python init_db.py
echo.

echo 3. 启动Flask应用...
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务
echo ====================================
echo.

python app.py

pause
