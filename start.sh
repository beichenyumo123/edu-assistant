#!/usr/bin/env bash
# EduAssistant 一键启动（macOS / Linux）
# Windows 用户请双击 start.bat 或运行: python start.py
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# 检查是否存在 Python 3
if command -v python3 &>/dev/null; then
  PYTHON=python3
elif command -v python &>/dev/null; then
  PYTHON=python
else
  echo "错误：未找到 Python，请先安装 Python 3.9+"
  echo "下载地址：https://www.python.org/downloads/"
  exit 1
fi

exec "$PYTHON" start.py "$@"
