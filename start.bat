@echo off
:: EduAssistant 一键启动（Windows）
:: 双击运行，或在终端中运行: start.bat
cd /d "%~dp0"

:: 查找 Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未找到 Python，请先安装 Python 3.9+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

python start.py %*
if %errorlevel% neq 0 (
    pause
)
