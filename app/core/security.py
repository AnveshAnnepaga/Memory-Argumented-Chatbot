# File: app/core/security.py
"""
Security and Authentication Module
Provides JWT-based authentication, password hashing, user management,
and protected route dependencies for the Vyron Intelligence Engine.
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import jwt, JWTError
import bcrypt as _bcrypt
from pydantic import BaseModel, EmailStr, Field
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.config import settings
from app.database.postgres import postgres_manager
from app.repositories.postgres.user_repository import UserTable

logger = logging.getLogger("app.core.security")

# JWT Configuration
SECRET_KEY = getattr(settings, "SECRET_KEY", "change-me-in-production-super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
REFRESH_TOKEN_EXPIRE_DAYS = 30

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


# ============================================================
# Pydantic Models
# ============================================================

class TokenData(BaseModel):
    """JWT token payload."""
    sub: str  # user_id
    email: str
    exp: int
    iat: int
    type: str = "access"  # "access" or "refresh"


class TokenResponse(BaseModel):
    """Token response for login/register."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserCreate(BaseModel):
    """User registration input."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)


class UserLogin(BaseModel):
    """User login input."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User profile response (no sensitive data)."""
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class UserInDB(BaseModel):
    """User model with hashed password for database."""
    id: str
    email: str
    full_name: Optional[str]
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    last_ip: Optional[str] = None

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class APIKeyResponse(BaseModel):
    """API key response."""
    id: str
    name: str
    key_prefix: str
    created_at: datetime
    last_used: Optional[datetime]
    expires_at: Optional[datetime]


# ============================================================
# Utility Functions
# ============================================================

def generate_user_id() -> str:
    """Generate unique user ID."""
    return f"usr_{secrets.token_urlsafe(16)}"


def generate_api_key() -> tuple[str, str]:
    """Generate API key and its prefix for display."""
    key = f"vyr_{secrets.token_urlsafe(32)}"
    prefix = f"vyr_{secrets.token_urlsafe(4)}..."
    return key, prefix


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return _bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(**payload)
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def create_token_pair(user_id: str, email: str) -> tuple[str, str]:
    """Create access and refresh token pair."""
    data = {"sub": user_id, "email": email}
    access = create_access_token(data)
    refresh = create_refresh_token(data)
    return access, refresh


# ============================================================
# User Management (PostgreSQL + In-Memory Fallback)
# ============================================================

# In-memory fallback for stub/offline mode when PostgreSQL is unavailable
_users_db: Dict[str, UserInDB] = {}
_email_to_id: Dict[str, str] = {}


def _row_to_user_in_db(row: UserTable) -> UserInDB:
    """Map a UserTable ORM row to a UserInDB model."""
    return UserInDB(
        id=row.id,
        email=row.email,
        full_name=row.full_name,
        hashed_password=row.password_hash,
        is_active=row.is_active,
        is_verified=getattr(row, 'is_verified', False),
        created_at=row.created_at.replace(tzinfo=None) if row.created_at else datetime.utcnow(),
        updated_at=row.updated_at.replace(tzinfo=None) if row.updated_at else datetime.utcnow(),
        last_login=row.last_login.replace(tzinfo=None) if row.last_login else None,
        last_ip=row.last_ip,
    )


async def _get_db_session():
    """Get a PostgreSQL session if available, otherwise None."""
    async for session in postgres_manager.get_session():
        return session
    return None


async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """Get user by ID from PostgreSQL (fallback to in-memory)."""
    session = await _get_db_session()
    if session is not None:
        try:
            stmt = select(UserTable).where(UserTable.id == user_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row:
                return _row_to_user_in_db(row)
        except Exception as exc:
            logger.warning(f"DB get_user_by_id error, falling back to memory: {exc}")
    return _users_db.get(user_id)


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user by email from PostgreSQL (fallback to in-memory)."""
    session = await _get_db_session()
    if session is not None:
        try:
            stmt = select(UserTable).where(UserTable.email == email.lower())
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row:
                return _row_to_user_in_db(row)
        except Exception as exc:
            logger.warning(f"DB get_user_by_email error, falling back to memory: {exc}")
    user_id = _email_to_id.get(email.lower())
    if user_id:
        return _users_db.get(user_id)
    return None


async def create_user(user_data: UserCreate, ip: Optional[str] = None, is_active: bool = True) -> UserInDB:
    """Create new user in PostgreSQL (fallback to in-memory)."""
    existing = await get_user_by_email(user_data.email)
    if existing and existing.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    if existing and not existing.is_active:
        # Reactivate deactivated account and update credentials
        existing.hashed_password = hash_password(user_data.password)
        existing.full_name = user_data.full_name
        existing.is_active = is_active
        existing.is_verified = False
        existing.updated_at = datetime.utcnow()
        existing.last_ip = ip

        session = await _get_db_session()
        if session is not None:
            try:
                stmt = select(UserTable).where(UserTable.email == user_data.email.lower())
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if row:
                    row.password_hash = existing.hashed_password
                    row.full_name = user_data.full_name
                    row.is_active = is_active
                    row.is_verified = False
                    row.updated_at = existing.updated_at
                    row.last_ip = ip
                    await session.commit()
            except Exception as exc:
                await session.rollback()
                logger.warning(f"DB reactivate_user error: {exc}")

        _users_db[existing.id] = existing
        _email_to_id[user_data.email.lower()] = existing.id
        return existing

    user_id = generate_user_id()
    now = datetime.utcnow()

    user = UserInDB(
        id=user_id,
        email=user_data.email.lower(),
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        is_active=is_active,
        is_verified=False,
        created_at=now,
        updated_at=now,
        last_ip=ip,
    )

    session = await _get_db_session()
    if session is not None:
        try:
            row = UserTable(
                id=user_id,
                username=user_data.email.lower(),
                email=user_data.email.lower(),
                password_hash=user.hashed_password,
                full_name=user_data.full_name,
                is_active=is_active,
                is_superuser=False,
                is_verified=False,
                created_at=now,
                updated_at=now,
                last_ip=ip,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            logger.info(f"Created user in PostgreSQL: {user_id} ({user_data.email})")
            return user
        except Exception as exc:
            await session.rollback()
            logger.warning(f"DB create_user error, falling back to memory: {exc}")

    _users_db[user_id] = user
    _email_to_id[user_data.email.lower()] = user_id
    logger.info(f"Created user in memory: {user_id} ({user_data.email})")
    return user


async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with email and password."""
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please register again with the same email to reactivate."
        )
    return user


async def update_last_login(user_id: str, ip: Optional[str] = None) -> None:
    """Update user's last login timestamp in PostgreSQL (fallback to in-memory)."""
    now = datetime.utcnow()
    session = await _get_db_session()
    if session is not None:
        try:
            stmt = select(UserTable).where(UserTable.id == user_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row:
                row.last_login = now
                row.last_ip = ip
                row.updated_at = now
                await session.commit()
                return
        except Exception as exc:
            logger.warning(f"DB update_last_login error, falling back to memory: {exc}")
    if user_id in _users_db:
        _users_db[user_id].last_login = now
        _users_db[user_id].last_ip = ip
        _users_db[user_id].updated_at = now


async def change_password(user_id: str, current_password: str, new_password: str) -> bool:
    """Change user password in PostgreSQL (fallback to in-memory)."""
    user = await get_user_by_id(user_id)
    if not user:
        return False
    if not verify_password(current_password, user.hashed_password):
        return False

    new_hash = hash_password(new_password)
    now = datetime.utcnow()

    session = await _get_db_session()
    if session is not None:
        try:
            stmt = select(UserTable).where(UserTable.id == user_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row:
                row.password_hash = new_hash
                row.updated_at = now
                await session.commit()
                return True
        except Exception as exc:
            logger.warning(f"DB change_password error, falling back to memory: {exc}")

    if user_id in _users_db:
        _users_db[user_id].hashed_password = new_hash
        _users_db[user_id].updated_at = now
        return True
    return False


async def deactivate_user(user_id: str) -> bool:
    """Deactivate user account in PostgreSQL (fallback to in-memory)."""
    now = datetime.utcnow()
    session = await _get_db_session()
    if session is not None:
        try:
            stmt = select(UserTable).where(UserTable.id == user_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row:
                row.is_active = False
                row.updated_at = now
                await session.commit()
                return True
        except Exception as exc:
            logger.warning(f"DB deactivate_user error, falling back to memory: {exc}")
    if user_id in _users_db:
        _users_db[user_id].is_active = False
        _users_db[user_id].updated_at = now
        return True
    return False


# ============================================================
# FastAPI Dependencies
# ============================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserInDB:
    """Get current authenticated user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token_data = decode_token(credentials.credentials)
    if not token_data or token_data.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = await get_user_by_id(token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserInDB]:
    """Get current user if authenticated, otherwise None."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Get current active user (must be active)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


# ============================================================
# Rate Limiting (Simple in-memory)
# ============================================================

_rate_limit_store: Dict[str, List[datetime]] = {}


def check_rate_limit(
    key: str,
    limit: int = 60,
    window_seconds: int = 60
) -> bool:
    """Check if request is within rate limit."""
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=window_seconds)

    if key not in _rate_limit_store:
        _rate_limit_store[key] = []

    # Clean old entries
    _rate_limit_store[key] = [
        ts for ts in _rate_limit_store[key] if ts > window_start
    ]

    if len(_rate_limit_store[key]) >= limit:
        return False

    _rate_limit_store[key].append(now)
    return True


# ============================================================
# Data Encryption Utilities (for sensitive user data)
# ============================================================

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data (placeholder - use proper encryption in production)."""
    # In production, use Fernet or AES-GCM with proper key management
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def mask_email(email: str) -> str:
    """Mask email for logging/display."""
    parts = email.split("@")
    if len(parts) == 2:
        return f"{parts[0][:2]}***@{parts[1]}"
    return "***"


def mask_ip(ip: str) -> str:
    """Mask IP address for logging."""
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.*.{parts[3]}"
    return "*.*.*.*"


# ============================================================
# Input Sanitization
# ============================================================

def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input to prevent injection."""
    if not text:
        return ""
    # Remove null bytes and control characters
    cleaned = text.replace("\x00", "").strip()
    # Limit length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    import re
    # Remove path traversal attempts
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    # Keep only safe characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return filename[:255]


# ============================================================
# API Key Management
# ============================================================

_api_keys: Dict[str, Dict[str, Any]] = {}


async def create_api_key(
    user_id: str,
    name: str,
    expires_days: Optional[int] = None
) -> tuple[str, str]:
    """Create new API key for user."""
    key, prefix = generate_api_key()
    key_id = f"key_{secrets.token_urlsafe(16)}"
    expires_at = None
    if expires_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

    _api_keys[key] = {
        "id": key,
        "prefix": key[:8] + "...",
        "name": name,
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "last_used": None
    }
    return key, f"agt_{key[:8]}..."


async def validate_api_key(key: str) -> Optional[str]:
    """Validate API key and return user_id if valid."""
    if key not in _api_keys:
        return None
    key_data = _api_keys[key]
    if key_data.get("expires_at") and datetime.utcnow() > key_data["expires_at"]:
        return None
    # Update last used
    _api_keys[key]["last_used"] = datetime.utcnow()
    return key_data["user_id"]


# ============================================================
# Audit Logging
# ============================================================

_audit_logs: List[Dict[str, Any]] = []


async def audit_log(
    user_id: Optional[str],
    action: str,
    resource: str,
    details: Optional[Dict[str, Any]] = None,
    ip: Optional[str] = None,
    success: bool = True
) -> None:
    """Log audit event."""
    _audit_logs.append({
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "details": details or {},
        "ip": mask_ip(ip) if ip else None,
        "success": success
    })
    # Keep only last 10000 logs in memory
    if len(_audit_logs) > 10000:
        _audit_logs[:] = _audit_logs[-10000:]


# ============================================================
# Export all for easy imports
# ============================================================

__all__ = [
    # Token models
    "TokenData", "TokenResponse",
    "UserCreate", "UserLogin", "UserResponse", "UserInDB",
    "PasswordChange", "APIKeyResponse",
    # Functions
    "hash_password", "verify_password",
    "create_access_token", "create_refresh_token",
    "create_token_pair", "decode_token",
    "get_user_by_id", "get_user_by_email",
    "create_user", "authenticate_user",
    "update_last_login", "change_password",
    "deactivate_user",
    # Dependencies
    "get_current_user", "get_current_user_optional",
    "get_current_active_user",
    # Rate limiting
    "check_rate_limit",
    # Encryption
    "encrypt_sensitive_data", "mask_email", "mask_ip",
    # Sanitization
    "sanitize_input", "sanitize_filename",
    # API Keys
    "create_api_key", "validate_api_key",
    # Audit
    "audit_log",
]