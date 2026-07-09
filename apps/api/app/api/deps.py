from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.entities import User


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = authorization.removeprefix("Bearer ").strip()
    subject = decode_access_token(token)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = db.get(User, subject)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or missing user",
        )
    return user

