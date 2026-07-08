"""
OnboardAgent - FastAPI 主入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import init_db
from .api import auth, files, chat, conversations, tools, memory
from .rag.embeddings import preload_embeddings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：初始化数据库
    init_db()
    print("⏳ 正在加载本地向量模型...")
    preload_embeddings()
    print(f"✅ 本地向量模型加载完成: {settings.LOCAL_EMBEDDING_MODEL}")
    print(f"✅ 数据库初始化完成")
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} 启动成功")
    print(f"📡 API文档: http://{settings.HOST}:{settings.PORT}/docs")
    yield
    # 关闭时：清理资源
    print("🛑 应用关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于 RAG 的企业新员工入职培训知识助手",
    lifespan=lifespan,
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(tools.router)
app.include_router(memory.router)


@app.get("/")
def root():
    """健康检查"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/api/health")
def health_check():
    """健康检查端点"""
    return {"status": "ok"}
