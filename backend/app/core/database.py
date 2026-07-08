"""
数据库模块
SQLAlchemy引擎 + Session管理 + 基类
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings

# 创建引擎 (SQLite: check_same_thread=False 允许跨线程)
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
)

# Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


def get_db():
    """FastAPI依赖注入：获取数据库Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_sqlite_column(table_name: str, column_name: str, column_definition: str) -> None:
    """为早期本地 SQLite 数据库补充新增列。"""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as conn:
        columns = conn.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
        existing_names = {column[1] for column in columns}
        if column_name not in existing_names:
            conn.exec_driver_sql(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            )


def init_db():
    """初始化数据库：创建所有表"""
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_column("messages", "agent_steps", "TEXT")
    _ensure_sqlite_column("messages", "evaluation", "TEXT")
    _ensure_sqlite_column("user_memories", "memory_enabled", "BOOLEAN DEFAULT 1")
