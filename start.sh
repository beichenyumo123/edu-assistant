#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

cleanup() {
  echo ""
  echo -e "${YELLOW}正在关闭服务...${NC}"
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
  wait 2>/dev/null
  echo -e "${GREEN}服务已关闭${NC}"
  exit 0
}
trap cleanup SIGINT SIGTERM

# ── Backend ──────────────────────────────────────────────
echo -e "${CYAN}[1/2] 启动后端...${NC}"

cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
  echo -e "${YELLOW}创建 Python 虚拟环境...${NC}"
  python3 -m venv venv
fi

source venv/bin/activate

if ! python -c "import fastapi" 2>/dev/null; then
  echo -e "${YELLOW}安装后端依赖...${NC}"
  pip install -r requirements.txt -q
fi

if [ ! -f ".env" ]; then
  echo -e "${YELLOW}未找到 .env，从 .env.example 复制...${NC}"
  cp .env.example .env
fi

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}后端已启动 (PID: $BACKEND_PID) → http://localhost:8000${NC}"
echo -e "${GREEN}API 文档 → http://localhost:8000/docs${NC}"

# ── Frontend ─────────────────────────────────────────────
echo ""
echo -e "${CYAN}[2/2] 启动前端...${NC}"

cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
  echo -e "${YELLOW}安装前端依赖...${NC}"
  npm install
fi

npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}前端已启动 (PID: $FRONTEND_PID) → http://localhost:5173${NC}"

# ── Ready ────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  EduAssistant 启动完成${NC}"
echo -e "${GREEN}  前端: http://localhost:5173${NC}"
echo -e "${GREEN}  后端: http://localhost:8000${NC}"
echo -e "${GREEN}  API:  http://localhost:8000/docs${NC}"
echo -e "${GREEN}  按 Ctrl+C 停止所有服务${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

wait
