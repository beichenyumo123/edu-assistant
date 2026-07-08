"""
认证API - 用户注册、登录、信息获取
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import hash_password, verify_password, create_access_token, decode_access_token
from ..models.user import User
from ..schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserUpdateRequest
from ..services.default_documents import ensure_default_onboarding_document

router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """从JWT Token中解析当前用户（依赖注入）"""
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token无效或已过期")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token格式错误")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已被注册")
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 创建用户
    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        grade=req.grade,
        major=req.major,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 新用户默认带入企业入职培训手册，方便开箱即用。
    # 初始化失败不阻断注册，避免默认资料缺失影响账号创建。
    try:
        ensure_default_onboarding_document(db, user)
    except Exception as exc:
        print(f"默认入职培训资料初始化失败: {exc}")

    # 生成Token
    token = create_access_token(data={"sub": str(user.id), "username": user.username})
    return TokenResponse(access_token=token, user=user.to_dict())


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(data={"sub": str(user.id), "username": user.username})
    return TokenResponse(access_token=token, user=user.to_dict())


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {"user": current_user.to_dict()}


@router.put("/me")
def update_me(
    req: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前登录用户信息"""
    username = req.username.strip()
    email = req.email.strip()
    grade = req.grade.strip() if req.grade else None
    major = req.major.strip() if req.major else None

    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    if not email:
        raise HTTPException(status_code=400, detail="邮箱不能为空")
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    existing_username = (
        db.query(User)
        .filter(User.username == username, User.id != current_user.id)
        .first()
    )
    if existing_username:
        raise HTTPException(status_code=400, detail="用户名已被使用")

    existing_email = (
        db.query(User)
        .filter(User.email == email, User.id != current_user.id)
        .first()
    )
    if existing_email:
        raise HTTPException(status_code=400, detail="邮箱已被使用")

    current_user.username = username
    current_user.email = email
    current_user.grade = grade
    current_user.major = major
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {"user": current_user.to_dict()}
