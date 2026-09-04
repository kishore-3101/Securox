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
SECUROX_ENV = os.getenv("SECUROX_ENV", "development").lower()
SECRET_KEY = os.getenv("SECRET_KEY", "")

# Production Fail-Fast Security Enforcement
DEFAULT_INSECURE_KEYS = {
    "securox-super-secret-key-change-in-production-2024",
    "secret",
    "changeme",
    "password",
    "admin"
}

def validate_production_secrets(env: Optional[str] = None, secret: Optional[str] = None):
    check_env = (env if env is not None else os.getenv("SECUROX_ENV", "development")).lower()
    check_secret = secret if secret is not None else os.getenv("SECRET_KEY", "")
    if check_env == "production":
        if not check_secret or check_secret in DEFAULT_INSECURE_KEYS or len(check_secret) < 32:
            raise RuntimeError(
                "FATAL SECURITY CONFIGURATION ERROR: Production environment detected with missing or insecure SECRET_KEY! "
                "A cryptographically strong SECRET_KEY (>= 32 characters) must be set via environment variable."
            )

validate_production_secrets(SECUROX_ENV, SECRET_KEY)

if SECUROX_ENV != "production" and not SECRET_KEY:
    SECRET_KEY = "securox-dev-local-secret-key-do-not-use-in-production-2026"

ALGORITHM  = "HS256"
TOKEN_EXPIRE_MINUTES = 480   # 8 hours

oauth2_scheme  = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
PBKDF2_ITERATIONS = 260_000


# ── User Context & Profile Attributes Registry ───────────────────────────────
USER_PROFILES = {
    "doctor": {
        "domain": "HEALTHCARE",
        "department": "Cardiology",
        "jurisdiction": None,
        "branch": None,
        "assigned_patients": ["P-1001", "P-1002", "P-1003"]
    },
    "nurse": {
        "domain": "HEALTHCARE",
        "department": "Cardiology",
        "jurisdiction": None,
        "branch": None,
        "assigned_patients": ["P-1001", "P-1002", "P-1003"]
    },
    "hospital_admin": {
        "domain": "HEALTHCARE",
        "department": "Administration",
        "jurisdiction": None,
        "branch": None,
        "assigned_patients": []
    },
    "traffic_operator": {
        "domain": "TRAFFIC",
        "department": "Traffic Operations",
        "jurisdiction": "Central",
        "branch": None,
        "assigned_patients": []
    },
    "traffic": {
        "domain": "TRAFFIC",
        "department": "Traffic Operations",
        "jurisdiction": "Central",
        "branch": None,
        "assigned_patients": []
    },
    "signal_tech": {
        "domain": "TRAFFIC",
        "department": "Traffic Signal Engineering",
        "jurisdiction": "Central",
        "branch": None,
        "assigned_patients": []
    },
    "customer": {
        "domain": "FINANCE",
        "department": "Retail",
        "jurisdiction": None,
        "branch": "Bengaluru_Central",
        "customer_id": "CUST-501",
        "assigned_patients": []
    },
    "branch_manager": {
        "domain": "FINANCE",
        "department": "Metro Central",
        "jurisdiction": None,
        "branch": "Metro Central",
        "assigned_patients": []
    },
    "teller": {
        "domain": "FINANCE",
        "department": "Metro Central",
        "jurisdiction": None,
        "branch": "Metro Central",
        "assigned_patients": []
    },
    "fraud_analyst": {
        "domain": "FINANCE",
        "department": "Fraud Risk Investigation",
        "jurisdiction": "ALL",
        "branch": "ALL",
        "assigned_patients": []
    },
    "finance": {
        "domain": "FINANCE",
        "department": "Fraud Risk Investigation",
        "jurisdiction": "ALL",
        "branch": "ALL",
        "assigned_patients": []
    },
    "auditor": {
        "domain": "GLOBAL",
        "department": "Internal Audit",
        "jurisdiction": "ALL",
        "branch": "ALL",
        "assigned_patients": []
    },
    "soc_analyst": {
        "domain": "SOC",
        "department": "Cyber Defense",
        "jurisdiction": "ALL",
        "branch": "ALL",
        "assigned_patients": []
    },
    "analyst": {
        "domain": "SOC",
        "department": "Cyber Defense",
        "jurisdiction": "ALL",
        "branch": "ALL",
        "assigned_patients": []
    },
    "admin": {
        "domain": "GLOBAL",
        "department": "City Administration",
        "jurisdiction": "ALL",
        "branch": "ALL",
        "assigned_patients": []
    },
    "superadmin": {
        "domain": "GLOBAL",
        "department": "Executive Command",
        "jurisdiction": "ALL",
        "branch": "ALL",
        "assigned_patients": []
    }
}


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
    
    # Automatically attach user profile claims if available
    sub = to_encode.get("sub")
    if sub and sub in USER_PROFILES:
        prof = USER_PROFILES[sub]
        to_encode.setdefault("domain", prof.get("domain", "GLOBAL"))
        to_encode.setdefault("department", prof.get("department"))
        to_encode.setdefault("jurisdiction", prof.get("jurisdiction"))
        to_encode.setdefault("branch", prof.get("branch"))
        to_encode.setdefault("customer_id", prof.get("customer_id"))
        to_encode.setdefault("assigned_patients", prof.get("assigned_patients", []))

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── dependency ────────────────────────────────────────────────────────────────
async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        payload   = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username  = payload.get("sub")
        role      = payload.get("role", "viewer")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        user = store.get_user(username)
        if not user or not user.get("is_active", 1):
            raise HTTPException(status_code=401, detail="User is inactive or missing")
        
        # Merge DB attributes and profile attributes
        profile = USER_PROFILES.get(username, USER_PROFILES.get(role, {}))
        return {
            "id": user.get("id", username),
            "username": username,
            "role": role,
            "full_name": user.get("full_name", username),
            "domain": payload.get("domain", profile.get("domain", "GLOBAL")),
            "department": payload.get("department", profile.get("department")),
            "jurisdiction": payload.get("jurisdiction", profile.get("jurisdiction")),
            "branch": payload.get("branch", profile.get("branch")),
            "customer_id": payload.get("customer_id", profile.get("customer_id")),
            "assigned_patients": payload.get("assigned_patients", profile.get("assigned_patients", []))
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_optional_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[dict]:
    """Optional authentication for public routes that adapt behavior when authenticated."""
    if not token:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None

async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin role required")
    return current_user

def require_roles(*roles: str):
    async def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles and current_user["role"] not in ("admin", "superadmin"):
            raise HTTPException(status_code=403, detail=f"Required role: one of {', '.join(roles)}")
        return current_user
    return dependency

def decode_token_or_none(token: Optional[str]) -> Optional[dict]:
    """Helper to decode a JWT token string or return None if invalid/expired."""
    if not token:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None

