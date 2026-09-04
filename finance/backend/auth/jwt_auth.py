"""
Securox — JWT Authentication & RBAC
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from database.store import store
import os
import hashlib
import hmac
import secrets

# ── config ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "securox-super-secret-key-change-in-production-2024")
ALGORITHM  = "HS256"
TOKEN_EXPIRE_MINUTES = 480   # 8 hours

oauth2_scheme  = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
PBKDF2_ITERATIONS = 260_000


# ── models ────────────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type:   str
    role:         str
    username:     str

class TokenData(BaseModel):
    username: Optional[str] = None
    role:     Optional[str] = None


# ── helpers ───────────────────────────────────────────────────────────────────
def verify_password(plain: str, hashed: str) -> bool:
    try:
        scheme, iterations, salt, digest = hashed.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            plain.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(candidate, digest)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = secrets.token_urlsafe(18)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"

def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = store.get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── dependency ────────────────────────────────────────────────────────────────
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    if not token:
        return {"username": "local_viewer", "role": "viewer"}
    try:
        payload   = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username  = payload.get("sub")
        role      = payload.get("role", "viewer")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = store.get_user(username)
        if not user or not user.get("is_active", 1):
            raise HTTPException(status_code=401, detail="User is inactive or missing")
        return {"username": username, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin role required")
    return current_user

def require_roles(*roles: str):
    async def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail=f"Required role: one of {', '.join(roles)}")
        return current_user
    return dependency
