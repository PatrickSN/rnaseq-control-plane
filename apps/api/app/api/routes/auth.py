from __future__ import annotations

from typing import Annotated, TypeAlias

from fastapi import APIRouter, Depends, HTTPException, status
from rnaseq_contracts import AuthLogin, TokenRead, UserCreate, UserRead
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.entities import AuditEvent, User

router = APIRouter(prefix="/api/auth", tags=["auth"])
DbSession: TypeAlias = Annotated[Session, Depends(get_db)]
CurrentUser: TypeAlias = Annotated[User, Depends(get_current_user)]


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=str(payload.email),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role="user",
    )
    db.add(user)
    db.flush()
    db.add(
        AuditEvent(
            user_id=user.id,
            action="auth.register",
            entity_type="user",
            entity_id=user.id,
            payload={"email": user.email},
        )
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenRead)
def login(payload: AuthLogin, db: DbSession) -> TokenRead:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    db.add(
        AuditEvent(
            user_id=user.id,
            action="auth.login",
            entity_type="user",
            entity_id=user.id,
            payload={},
        )
    )
    db.commit()
    return TokenRead(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> User:
    return current_user
