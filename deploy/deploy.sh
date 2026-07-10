#!/usr/bin/env bash
# ============================================================
# OnboardAgent 一键部署脚本（在阿里云 ECS 上运行）
#
# 用法：
#   chmod +x deploy.sh
#   sudo ./deploy.sh
#
# 前提：已安装 git，已克隆项目到 /opt/onboardagent
# ============================================================

set -euo pipefail

# ── 配置变量 ──────────────────────────────────────────────────
APP_DIR="/opt/onboardagent"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"
LOG_DIR="/var/log/onboardagent"
NGINX_CONF="/etc/nginx/sites-available/onboardagent"
NGINX_ENABLED="/etc/nginx/sites-enabled/onboardagent"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

step()  { echo -e "\n${CYAN}==> $1${NC}"; }
ok()    { echo -e "${GREEN}  ✓ $1${NC}"; }
warn()  { echo -e "${YELLOW}  ⚠ $1${NC}"; }
err()   { echo -e "${RED}  ✗ $1${NC}"; exit 1; }

# ── 权限检查 ──────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    err "请用 sudo 运行此脚本: sudo ./deploy.sh"
fi

echo -e "${GREEN}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║     OnboardAgent 一键部署                ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. 系统依赖 ──────────────────────────────────────────────
step "1/9 安装系统依赖..."

# 检测包管理器
if command -v apt &>/dev/null; then
    PKG_MGR="apt"
    apt update -qq
elif command -v yum &>/dev/null; then
    PKG_MGR="yum"
else
    err "不支持的系统，请手动安装依赖"
fi

# Python 3.11+
if ! command -v python3.11 &>/dev/null; then
    echo "  正在安装 Python 3.11..."
    if [[ $PKG_MGR == "apt" ]]; then
        add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
        apt install -y -qq python3.11 python3.11-venv python3.11-dev
    else
        yum install -y python3.11 python3.11-devel
    fi
fi
ok "Python $(python3.11 --version)"

# Nginx
if ! command -v nginx &>/dev/null; then
    echo "  正在安装 Nginx..."
    if [[ $PKG_MGR == "apt" ]]; then
        apt install -y -qq nginx
    else
        yum install -y nginx
    fi
fi
ok "Nginx $(nginx -v 2>&1)"

# Git
if ! command -v git &>/dev/null; then
    if [[ $PKG_MGR == "apt" ]]; then
        apt install -y -qq git
    else
        yum install -y git
    fi
fi
ok "Git $(git --version | awk '{print $3}')"

# ── 2. 创建目录结构 ──────────────────────────────────────────
step "2/9 创建目录结构..."
mkdir -p "$APP_DIR" "$LOG_DIR"
chown -R "$SUDO_USER:$SUDO_USER" "$APP_DIR"
ok "应用目录: $APP_DIR"
ok "日志目录: $LOG_DIR"

# ── 3. Python 虚拟环境 ──────────────────────────────────────
step "3/9 创建 Python 虚拟环境..."
if [[ ! -d "$VENV_DIR" ]]; then
    sudo -u "$SUDO_USER" python3.11 -m venv "$VENV_DIR"
fi
ok "虚拟环境: $VENV_DIR"

echo "  安装 Python 依赖..."
sudo -u "$SUDO_USER" "$VENV_DIR/bin/pip" install -q --upgrade pip
sudo -u "$SUDO_USER" "$VENV_DIR/bin/pip" install -q -r "$BACKEND_DIR/requirements.txt"
sudo -u "$SUDO_USER" "$VENV_DIR/bin/pip" install -q gunicorn
ok "Python 依赖安装完成"

# ── 4. 环境配置 ──────────────────────────────────────────────
step "4/9 配置环境变量..."
if [[ ! -f "$BACKEND_DIR/.env" ]]; then
    if [[ -f "$APP_DIR/deploy/.env.production" ]]; then
        cp "$APP_DIR/deploy/.env.production" "$BACKEND_DIR/.env"
        warn "已从模板创建 .env，请编辑 $BACKEND_DIR/.env 填入真实值！"
        warn "特别注意修改: SECRET_KEY、CORS_ORIGINS、DEEPSEEK_API_KEY"
    else
        err "找不到 deploy/.env.production 模板"
    fi
else
    ok ".env 已存在，跳过"
fi

# ── 5. 下载向量模型 ──────────────────────────────────────────
step "5/9 下载向量模型（首次较慢，约 400MB）..."
MODEL_NAME="BAAI/bge-small-zh-v1.5"

# 检查模型是否已在缓存中
MODEL_CACHED=$(
    cd "$BACKEND_DIR" && \
    sudo -u "$SUDO_USER" "$VENV_DIR/bin/python" -c "
from sentence_transformers import SentenceTransformer
try:
    SentenceTransformer('$MODEL_NAME', local_files_only=True)
    print('yes')
except Exception:
    print('no')
" 2>/dev/null
)

if [[ "$MODEL_CACHED" == "yes" ]]; then
    ok "向量模型已缓存，跳过下载"
else
    echo "  正在下载 $MODEL_NAME（使用 hf-mirror.com 镜像）..."
    # 临时允许联网下载
    sudo -u "$SUDO_USER" "$VENV_DIR/bin/python" -c "
import os
# 允许联网下载
os.environ.pop('HF_HUB_OFFLINE', None)
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ.pop('TRANSFORMERS_OFFLINE', None)
from sentence_transformers import SentenceTransformer
print('正在下载模型...')
SentenceTransformer('$MODEL_NAME')
print('下载完成')
"
    ok "向量模型下载完成"
fi

# ── 6. 构建前端 ──────────────────────────────────────────────

# ── 5.5. 预向量化默认培训资料 ──────────────────────────────────
step "5.5/9 预向量化默认企业培训资料到共享知识库..."
sudo -u "$SUDO_USER" "$VENV_DIR/bin/python" "$APP_DIR/deploy/seed_shared_docs.py"
ok "默认培训资料已向量化"

step "6/9 构建前端..."

# 检查 Node.js
if ! command -v node &>/dev/null && ! command -v nodejs &>/dev/null; then
    echo "  正在安装 Node.js..."
    if [[ $PKG_MGR == "apt" ]]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt install -y -qq nodejs
    else
        curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -
        yum install -y nodejs
    fi
fi

NODE_CMD=$(command -v node || command -v nodejs)
ok "Node.js $($NODE_CMD --version)"

cd "$FRONTEND_DIR"
if [[ ! -d "node_modules" ]]; then
    sudo -u "$SUDO_USER" npm install
fi
sudo -u "$SUDO_USER" npm run build
ok "前端构建完成 → $FRONTEND_DIR/dist/"

# ── 7. 配置 Nginx ────────────────────────────────────────────
step "7/9 配置 Nginx..."

# 对于 Ubuntu/Debian，使用 sites-available；对于 CentOS/RHEL，直接用 conf.d
if [[ -d "/etc/nginx/sites-available" ]]; then
    cp "$APP_DIR/deploy/nginx.conf" "$NGINX_CONF"
    ln -sf "$NGINX_CONF" "$NGINX_ENABLED"
    # 删除默认站点
    rm -f /etc/nginx/sites-enabled/default
else
    cp "$APP_DIR/deploy/nginx.conf" "/etc/nginx/conf.d/onboardagent.conf"
fi

# 确保 nginx 用户能访问项目目录
chmod o+x "$APP_DIR" "$APP_DIR/frontend" "$APP_DIR/frontend/dist"

# 测试配置
if nginx -t 2>&1; then
    ok "Nginx 配置验证通过"
else
    err "Nginx 配置有误，请检查"
fi

# ── 8. 配置 systemd 服务 ─────────────────────────────────────
step "8/9 配置 systemd 服务..."
cp "$APP_DIR/deploy/onboardagent.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable onboardagent

# 重启服务
echo "  重启服务..."
systemctl restart onboardagent || warn "后端服务启动失败，请检查日志"
systemctl restart nginx || warn "Nginx 启动失败，请检查日志"

sleep 2

# ── 验证部署 ─────────────────────────────────────────────────
echo -e "\n${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"

# 检查服务状态
echo -e "\n${CYAN}服务状态:${NC}"
systemctl is-active onboardagent &>/dev/null && echo -e "  $(ok "后端: 运行中")" || echo -e "  $(err "后端: 未运行")"
systemctl is-active nginx &>/dev/null && echo -e "  $(ok "Nginx: 运行中")" || echo -e "  $(err "Nginx: 未运行")"

# 健康检查
echo -e "\n${CYAN}健康检查:${NC}"
sleep 1
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/health 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
    ok "后端 API: http://127.0.0.1:8000/api/health → $HTTP_CODE"
else
    warn "后端 API 返回 $HTTP_CODE，请检查日志: journalctl -u onboardagent -n 50"
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
    ok "前端页面: http://127.0.0.1/ → $HTTP_CODE"
else
    warn "前端页面返回 $HTTP_CODE"
fi

echo -e "\n${YELLOW}下一步:${NC}"
echo "  1. 编辑 .env:  vi $BACKEND_DIR/.env"
echo "  2. 修改 SECRET_KEY 和 CORS_ORIGINS"
echo "  3. 查看日志:  journalctl -u onboardagent -f"
echo "  4. 查看 Nginx 日志: tail -f /var/log/nginx/access.log"
echo ""
echo -e "${GREEN}🎉 访问 http://<你的服务器IP> 开始使用！${NC}"
