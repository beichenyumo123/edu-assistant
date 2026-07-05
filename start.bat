@echo off
:: EduAssistant 一键启动（Windows）
:: 双击运行，或在终端中运行: start.bat
cd /d "%~dp0"

:: 查找 Python 3.11
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    goto run_py_launcher
)

python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未找到 Python 3.11。项目后端请使用 Python 3.11。
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

python start.py %*
if errorlevel 1 (
    pause
)
exit /b %errorlevel%

:run_py_launcher
py -3.11 start.py %*
if errorlevel 1 (
    pause
)
exit /b %errorlevel%
