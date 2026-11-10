import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import RefreshToken, User, UserRole
from app.store_access import merchant_store_id
from app.security import create_token, current_user, hash_password, verify_password
from app.rate_limit import check_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=8, max_length=40)
    default_address: str = Field(min_length=5, max_length=500)
    privacy_consent: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


def _set_cookies(response: Response, tokens: dict, request: Request) -> None:
    if request.headers.get("X-SG-Browser-Session") != "1":
        return
    secure = request.url.scheme == "https"
    response.set_cookie("sg_access", tokens["access_token"], httponly=True, secure=secure, samesite="lax", max_age=get_settings().jwt_access_token_minutes * 60)
    response.set_cookie("sg_refresh", tokens["refresh_token"], httponly=True, secure=secure, samesite="lax", path="/api/v1/auth", max_age=get_settings().jwt_refresh_token_days * 86400)


def user_response(user: User, db: Session) -> dict:
    store_id = merchant_store_id(db, user) if user.role == UserRole.MERCHANT else None
    return {"id": str(user.id), "email": user.email, "full_name": user.full_name,
            "role": user.role.value, "store_id": str(store_id) if store_id else None,
            "phone": user.phone, "default_address": user.default_address}


def _issue_tokens(user: User, db: Session) -> dict:
    settings = get_settings()
    refresh = create_token(user, token_type="refresh", expires_delta=timedelta(days=settings.jwt_refresh_token_days))
    db.add(RefreshToken(user_id=user.id, token_hash=hashlib.sha256(refresh.encode()).hexdigest(), expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_days)))
    access = create_token(user, token_type="access", expires_delta=timedelta(minutes=settings.jwt_access_token_minutes))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "user": user_response(user, db)}


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    check_rate_limit(f"auth:register:{payload.email}", limit=5, window_seconds=3600)
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    if not payload.privacy_consent:
        raise HTTPException(status_code=422, detail="Privacy consent is required")
    user = User(email=payload.email, password_hash=hash_password(payload.password), full_name=payload.full_name,
                phone=payload.phone, default_address=payload.default_address,
                privacy_consent_at=datetime.now(timezone.utc), role=UserRole.CUSTOMER)
    db.add(user)
    db.commit()
    db.refresh(user)
    tokens = _issue_tokens(user, db)
    db.commit()
    _set_cookies(response, tokens, request)
    return {"user": tokens["user"]} if request.headers.get("X-SG-Browser-Session") == "1" else tokens


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    check_rate_limit(f"auth:login:{payload.email}", limit=5, window_seconds=60)
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    tokens = _issue_tokens(user, db)
    db.commit()
    _set_cookies(response, tokens, request)
    return {"user": tokens["user"]} if request.headers.get("X-SG-Browser-Session") == "1" else tokens


@router.post("/refresh")
def refresh(request: Request, response: Response, payload: RefreshRequest | None = None, db: Session = Depends(get_db)) -> dict:
    refresh_token = (payload.refresh_token if payload else None) or request.cookies.get("sg_refresh")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token required")
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update())
    if stored is None or stored.revoked_at is not None or stored.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    stored.revoked_at = datetime.now(timezone.utc)
    tokens = _issue_tokens(user, db)
    db.commit()
    _set_cookies(response, tokens, request)
    return {"user": tokens["user"]} if request.headers.get("X-SG-Browser-Session") == "1" else tokens


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    refresh_token = request.cookies.get("sg_refresh")
    if refresh_token:
        stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hashlib.sha256(refresh_token.encode()).hexdigest()))
        if stored:
            stored.revoked_at = datetime.now(timezone.utc)
            db.commit()
    response.delete_cookie("sg_access")
    response.delete_cookie("sg_refresh", path="/api/v1/auth")
    return {"status": "logged_out"}


@router.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return user_response(user, db)
