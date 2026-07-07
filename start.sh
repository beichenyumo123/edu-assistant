#!/usr/bin/env bash
# OnboardAgent 一键启动（macOS / Linux）
# Windows 用户请双击 start.bat 或运行: python start.py
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

is_python311() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)' >/dev/null 2>&1
}

# 项目约定使用 Python 3.11，避免误用系统 python3（如 3.13）。
if command -v python3.11 &>/dev/null && is_python311 python3.11; then
  PYTHON=python3.11
elif command -v python &>/dev/null && is_python311 python; then
  PYTHON=python
else
  echo "错误：未找到 Python 3.11。项目后端请使用 Python 3.11。"
  echo "如果使用 conda，可执行：conda create -n edu-assistant python=3.11"
  echo "然后：conda activate edu-assistant && ./start.sh"
  echo "下载地址：https://www.python.org/downloads/"
  exit 1
fi

exec "$PYTHON" start.py "$@"
