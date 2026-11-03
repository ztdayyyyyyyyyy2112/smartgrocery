from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import User, UserRole
from app.security import create_token, current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def user_response(user: User) -> dict:
    return {"id": str(user.id), "email": user.email, "full_name": user.full_name, "role": user.role.value}


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password), full_name=payload.full_name, role=UserRole.CUSTOMER)
    db.add(user)
    db.commit()
    db.refresh(user)
    settings = get_settings()
    return {"access_token": create_token(user, token_type="access", expires_delta=timedelta(minutes=settings.jwt_access_token_minutes)), "token_type": "bearer", "user": user_response(user)}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    settings = get_settings()
    return {"access_token": create_token(user, token_type="access", expires_delta=timedelta(minutes=settings.jwt_access_token_minutes)), "token_type": "bearer", "user": user_response(user)}


@router.get("/me")
def me(user: User = Depends(current_user)) -> dict:
    return user_response(user)
