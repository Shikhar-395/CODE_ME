import jwt
import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Response, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .database import get_db
from .model import User

SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "change-this-dev-secret")
COOKIE_NAME = "medium_session"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


def create_token(user_id: int) -> str:
    # Session tokens now expire instead of staying valid forever.
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode({"user_id": user_id, "exp": expires_at}, SECRET_KEY, algorithm="HS256")


def verify_token(token: str) -> int:
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return data["user_id"] 
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session")


def set_session_cookies(user_id: int, response: Response) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=create_token(user_id),
        max_age=60 * 60 * 24 * 7,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax"
    )


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = verify_token(token)
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
