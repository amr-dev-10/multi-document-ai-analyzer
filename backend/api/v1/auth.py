from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.security import create_access_token, hash_password, verify_password
from backend.core.config import settings
from backend.db.session import get_db
from backend.models.user import User
from backend.schemas.auth import AuthRequest, TokenResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
def register(payload: AuthRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id), timedelta(minutes=settings.access_token_expire_minutes))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: AuthRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(str(user.id), timedelta(minutes=settings.access_token_expire_minutes))
    return TokenResponse(access_token=token)

