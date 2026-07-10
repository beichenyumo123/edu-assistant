# OnboardAgent 阿里云部署指南

## 🏗 架构概览

```
浏览器 (HTTPS)
    │
    ▼
┌──────────────────────────────┐
│  Nginx (:80/:443)            │
│  ├── /           → 前端静态  │
│  ├── /api/*      → 后端代理  │
│  └── /ws/*       → WebSocket │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Gunicorn + Uvicorn (:8000)  │
│  FastAPI 后端                 │
│  ├── SQLite                  │
│  ├── ChromaDB (向量库)       │
│  └── BGE Embedding 模型      │
└──────────────────────────────┘
```

## 📋 前置准备

### 1. 阿里云 ECS 购买建议

| 配置项 | 推荐 | 最低 |
|--------|------|------|
| CPU | 2 vCPU | 1 vCPU（构建前端慢） |
| 内存 | **4 GB** | 2 GB（BGE 模型加载接近极限） |
| 系统盘 | 40 GB ESSD | 20 GB |
| 操作系统 | Ubuntu 24.04 LTS | Ubuntu 22.04 LTS |
| 带宽 | 按量计费 3-5 Mbps | 1 Mbps |

> 💰 **300 元代金券预算参考**：2 vCPU 4GB 约 ~200 元/月，可用 ~1.5 个月。如果想更省，选 1 vCPU 2GB (~70 元/月)，可用 ~4 个月，但内存较紧张。

### 2. ECS 创建关键步骤

1. 登录 [阿里云 ECS 控制台](https://ecs.console.aliyun.com/)
2. 点击「创建实例」
3. **地域**：选择离你最近的（如「华东 1（杭州）」）
4. **镜像**：选择 **Ubuntu 24.04 LTS**
5. **实例规格**：2 vCPU 4 GiB（如 ecs.c7.large）或 1 vCPU 2 GiB
6. **网络**：分配公网 IP
7. **安全组**：入方向开放以下端口：
   - `22` (SSH) — 来源 `0.0.0.0/0`
   - `80` (HTTP) — 来源 `0.0.0.0/0`
   - `443` (HTTPS，可选) — 来源 `0.0.0.0/0`
8. **登录凭证**：创建密钥对（推荐）或设置密码
9. 确认下单，使用代金券支付

### 3. （可选）域名 + SSL

如果有域名，在阿里云 DNS 解析中添加 A 记录指向 ECS 公网 IP：

| 记录类型 | 主机记录 | 记录值 |
|----------|----------|--------|
| A | @ | 你的 ECS 公网 IP |
| A | www | 你的 ECS 公网 IP |

> 获得 SSL 证书：阿里云提供**免费 DV 证书**（在「SSL 证书」控制台申请）。

---

## 🚀 部署步骤

### Step 1: SSH 登录服务器

```bash
# 使用密钥
ssh -i ~/.ssh/your-key.pem root@<ECS公网IP>

# 或使用密码（创建时设置的）
ssh root@<ECS公网IP>
```

### Step 2: 克隆项目

```bash
# 创建应用目录
mkdir -p /opt
cd /opt

# 克隆你的仓库（替换为实际地址）
git clone https://github.com/你的用户名/edu-assistant.git onboardagent
cd onboardagent
```

### Step 3: （可选但推荐）创建非 root 用户

```bash
adduser onboard --disabled-password
usermod -aG sudo onboard
chown -R onboard:onboard /opt/onboardagent

# 后续步骤可以用 onboard 用户 + sudo 执行
```

### Step 4: 编辑生产配置

```bash
# 复制并编辑生产环境变量
cp deploy/.env.production backend/.env
vi backend/.env
```

**必须修改的项：**

```ini
# 用以下命令生成随机密钥：
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=你的随机密钥

# 替换为你的域名或服务器 IP
CORS_ORIGINS=https://你的域名.com,http://你的服务器IP

# 你的 DeepSeek API Key
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
```

### Step 5: 运行部署脚本

```bash
chmod +x deploy/deploy.sh
sudo ./deploy/deploy.sh
```

脚本会自动完成：
- ✅ 安装 Python 3.11、Nginx、Node.js
- ✅ 创建 Python 虚拟环境
- ✅ 安装所有依赖
- ✅ 下载 BGE 向量模型（~400MB）
- ✅ 构建前端
- ✅ 配置 Nginx + systemd
- ✅ 启动所有服务

### Step 6: 验证部署

```bash
# 检查后端状态
sudo systemctl status onboardagent

# 检查 Nginx 状态
sudo systemctl status nginx

# 健康检查
curl http://127.0.0.1/api/health

# 访问
curl http://127.0.0.1/
```

浏览器打开 `http://<你的服务器公网IP>` 应该能看到登录页面。

---

## 🔧 常用运维命令

```bash
# 查看后端日志
sudo journalctl -u onboardagent -f

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/onboardagent/error.log

# 重启服务
sudo systemctl restart onboardagent
sudo systemctl restart nginx

# 查看资源占用
htop
df -h
```

---

## 📁 部署后文件结构

```
/opt/onboardagent/
├── backend/
│   ├── .env               # 生产环境变量
│   ├── venv/              # Python 虚拟环境
│   ├── data/
│   │   ├── chroma_db/     # 向量数据库
│   │   └── uploads/       # 用户上传文件
│   └── edu_assistant.db   # SQLite 数据库
├── frontend/
│   └── dist/              # 前端构建产物
└── deploy/                # 部署配置文件
```

---

## 🔐 安全加固清单

- [ ] 修改 `SECRET_KEY` 为随机字符串
- [ ] 设置 `DEBUG=False`
- [ ] `CORS_ORIGINS` 仅包含实际域名
- [ ] 防火墙仅开放 22/80/443
- [ ] 配置 fail2ban 防止 SSH 暴力破解
- [ ] 申请 SSL 证书，启用 HTTPS
- [ ] 定期备份 `edu_assistant.db` 和 `data/` 目录
- [ ] 更新 API Key（不在 .env 中硬编码生产密钥）

### 一键安全加固

```bash
# 安装 fail2ban
sudo apt install -y fail2ban
sudo systemctl enable --now fail2ban

# 配置防火墙（阿里云安全组已做，这里是双重保险）
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

---

## 🔄 更新部署

```bash
cd /opt/onboardagent
git pull

# 更新后端依赖（如有变化）
./backend/venv/bin/pip install -r backend/requirements.txt

# 重新构建前端
cd frontend && npm install && npm run build

# 重启服务
sudo systemctl restart onboardagent
sudo systemctl restart nginx
```

---

## ❓ 常见问题

### Q: 后端启动失败，日志显示找不到模型
```bash
# 手动下载模型
cd /opt/onboardagent/backend
./venv/bin/python -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('BAAI/bge-small-zh-v1.5')
"
```

### Q: Nginx 502 Bad Gateway
后端未启动或端口不匹配：
```bash
sudo journalctl -u onboardagent -n 50
sudo netstat -tlnp | grep 8000
```

### Q: WebSocket 连接失败
检查 Nginx 配置中 `/ws/` 的 proxy 设置是否正确包含 `Upgrade` 和 `Connection` 头。

### Q: 上传文件失败
检查 `client_max_body_size` 是否足够（默认 20MB），以及上传目录权限。
