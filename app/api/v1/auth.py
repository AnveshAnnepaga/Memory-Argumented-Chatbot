# File: app/api/v1/auth.py
"""
Authentication API Routes
Handles user registration, login, token management, profile, and history.
"""
from datetime import datetime
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.security import (
    get_current_user,
    get_current_user_optional,
    get_current_active_user,
    create_token_pair,
    decode_token,
    authenticate_user,
    create_user,
    update_last_login,
    change_password,
    deactivate_user,
    get_user_by_id,
    create_api_key,
    validate_api_key,
    audit_log,
    check_rate_limit,
    sanitize_input,
    UserCreate,
    UserLogin,
    UserResponse,
    UserInDB,
    TokenResponse,
    TokenData,
    PasswordChange,
    APIKeyResponse,
)
from app.core.config import settings
from app.database.postgres import postgres_manager
from app.repositories.postgres.user_repository import UserTable


logger = logging.getLogger("app.api.v1.auth")

router = APIRouter(tags=["Authentication"])


# ============================================================
# Request/Response Models
# ============================================================

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class HistoryItem(BaseModel):
    id: str
    query: str
    response: str
    route_type: str
    timestamp: datetime
    execution_time_ms: float
    tokens_used: int


class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int
    page: int
    page_size: int


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    expires_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    created_at: datetime
    expires_at: Optional[datetime]


# In-memory history store (replace with DB in production)
_user_history: dict[str, list[dict]] = {}
_user_sessions: dict[str, dict] = {}  # refresh_token -> {user_id, created_at}


# ============================================================
# Helper Functions
# ============================================================

def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def store_history(
    user_id: str,
    query: str,
    response: str,
    route_type: str,
    execution_time_ms: float,
    tokens_used: int
) -> None:
    """Store chat history for user."""
    if user_id not in _user_history:
        _user_history[user_id] = []

    entry = {
        "id": f"hist_{datetime.utcnow().timestamp()}",
        "query": query,
        "response": response,
        "route_type": route_type,
        "timestamp": datetime.utcnow(),
        "execution_time_ms": execution_time_ms,
        "tokens_used": tokens_used
    }

    _user_history[user_id].insert(0, entry)  # Most recent first

    # Keep last 1000 entries per user
    if len(_user_history[user_id]) > 1000:
        _user_history[user_id] = _user_history[user_id][:1000]


# ============================================================
# Authentication Routes
# ============================================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    response: Response,
    data: RegisterRequest
):
    """Register a new user and return auth tokens."""
    ip = get_client_ip(request)
    if not check_rate_limit(f"register:{ip}", limit=5, window_seconds=3600):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Try again later."
        )

    try:
        user = await create_user(
            UserCreate(email=data.email, password=data.password, full_name=data.full_name),
            is_active=True,
        )
    except HTTPException as e:
        await audit_log(None, "register", "user", {"email": data.email}, ip, False)
        raise e

    # Issue tokens
    access_token, refresh_token = create_token_pair(user.id, user.email)
    _user_sessions[refresh_token] = {"user_id": user.id, "created_at": datetime.utcnow()}

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    await audit_log(user.id, "register", "user", {"email": user.email}, ip, True)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 60 * 24 * 7,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=True,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    data: LoginRequest
):
    """Login user and return tokens."""
    ip = get_client_ip(request)

    # Rate limiting
    if not check_rate_limit(f"login:{ip}", limit=10, window_seconds=300):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later."
        )

    user = await authenticate_user(data.email, data.password)
    if not user:
        await audit_log(None, "login", "user", {"email": data.email}, ip, False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Update last login
    await update_last_login(user.id, get_client_ip(request))

    # Create tokens
    access_token, refresh_token = create_token_pair(user.id, user.email)

    # Store session
    _user_sessions[refresh_token] = {
        "user_id": user.id,
        "created_at": datetime.utcnow()
    }

    # Set secure cookies
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=60 * 60 * 24 * 30
    )

    await audit_log(user.id, "login", "user", {"email": user.email}, ip, True)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 60 * 24 * 7,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    data: RefreshRequest
):
    """Refresh access token using refresh token."""
    token_data = decode_token(data.refresh_token)
    if not token_data or token_data.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Verify session exists
    if data.refresh_token not in _user_sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )

    session = _user_sessions[data.refresh_token]
    user = await get_user_by_id(session["user_id"])
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    access_token, new_refresh = create_token_pair(user.id, user.email)

    # Rotate refresh token
    del _user_sessions[data.refresh_token]
    _user_sessions[new_refresh] = {
        "user_id": user.id,
        "created_at": datetime.utcnow()
    }

    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=60 * 60 * 24 * 30
    )

    await audit_log(user.id, "token_refresh", "token", {}, get_client_ip(request), True)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=60 * 60 * 24 * 7,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Logout user and invalidate session."""
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token and refresh_token in _user_sessions:
        del _user_sessions[refresh_token]

    # Clear cookie
    response.delete_cookie("refresh_token")

    await audit_log(current_user.id, "logout", "user", {}, get_client_ip(request), True)

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current user profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login
    )


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update user profile (full_name and/or email)."""
    user = await get_user_by_id(current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if email is not None:
        from app.repositories.postgres.user_repository import UserTable as UT
        session = None
        async for s in postgres_manager.get_session():
            session = s
            break
        if session is not None:
            stmt = select(UT).where(UT.email == email, UT.id != current_user.id)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                raise HTTPException(status_code=409, detail="Email already in use")
        email = email.strip().lower()

    now = datetime.utcnow()
    session = None
    async for s in postgres_manager.get_session():
        session = s
        break

    if session is not None:
        try:
            stmt = select(UserTable).where(UserTable.id == current_user.id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row:
                if full_name is not None:
                    row.full_name = full_name
                if email is not None:
                    row.email = email
                row.updated_at = now
                await session.commit()
                await session.refresh(row)
                return UserResponse(
                    id=row.id,
                    email=row.email,
                    full_name=row.full_name,
                    is_active=row.is_active,
                    created_at=row.created_at.replace(tzinfo=None) if row.created_at else now,
                    updated_at=row.updated_at.replace(tzinfo=None) if row.updated_at else now,
                    last_login=row.last_login.replace(tzinfo=None) if row.last_login else None
                )
        except Exception as exc:
            logger.warning(f"DB update_profile error: {exc}")

    from app.core.security import _users_db, _save_users_to_file
    if current_user.id in _users_db:
        if full_name is not None:
            _users_db[current_user.id].full_name = full_name
        if email is not None:
            _users_db[current_user.id].email = email
        _users_db[current_user.id].updated_at = now
        _save_users_to_file()

    db_user = _users_db.get(current_user.id, current_user)
    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        is_active=db_user.is_active,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at,
        last_login=db_user.last_login
    )


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Change user password."""
    success = await change_password(current_user.id, data.current_password, data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    await audit_log(current_user.id, "password_change", "user", {}, None, True)

    return {"message": "Password changed successfully"}


@router.delete("/me")
async def delete_account(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Deactivate user account (soft delete)."""
    await deactivate_user(current_user.id)
    await audit_log(current_user.id, "account_deletion", "user", {}, None, True)
    return {"message": "Account deactivated successfully"}


# ============================================================
# History Routes
# ============================================================

@router.get("/history", response_model=HistoryResponse)
async def get_history(
    page: int = 1,
    page_size: int = 20,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get user's chat history."""
    history = _user_history.get(current_user.id, [])

    # Pagination
    total = len(history)
    start = (page - 1) * page_size
    end = start + page_size
    items = history[start:end]

    return HistoryResponse(
        items=[HistoryItem(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/history")
async def clear_history(current_user: UserInDB = Depends(get_current_active_user)):
    """Clear user's chat history."""
    if current_user.id in _user_history:
        _user_history[current_user.id] = []

    await audit_log(current_user.id, "history_clear", "history", {}, None, True)

    return {"message": "History cleared successfully"}


@router.delete("/history/{item_id}")
async def delete_history_item(
    item_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete specific history item."""
    history = _user_history.get(current_user.id, [])
    original_len = len(history)
    _user_history[current_user.id] = [h for h in history if h["id"] != item_id]

    if len(_user_history[current_user.id]) == original_len:
        raise HTTPException(status_code=404, detail="History item not found")

    await audit_log(current_user.id, "history_delete", "history", {"item_id": item_id}, None, True)

    return {"message": "History item deleted"}


# ============================================================
# API Key Management
# ============================================================

@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create new API key for user."""
    from app.core.security import create_api_key

    key, prefix = await create_api_key(current_user.id, data.name, data.expires_days)

    return APIKeyResponse(
        id=key,
        name=data.name,
        key_prefix=f"vyr_{key[:8]}...",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=data.expires_days) if data.expires_days else None
    )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(current_user: UserInDB = Depends(get_current_active_user)):
    """List user's API keys (without full keys)."""
    from app.core.security import _api_keys

    keys = []
    for key, data in _api_keys.items():
        if data["user_id"] == current_user.id:
            keys.append(APIKeyResponse(
                id=data["id"],
                name=data["name"],
                key_prefix=data["prefix"],
                created_at=data["created_at"],
                expires_at=data.get("expires_at")
            ))
    return keys


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Revoke API key."""
    from app.core.security import _api_keys

    if key_id not in _api_keys:
        raise HTTPException(status_code=404, detail="API key not found")

    if _api_keys[key_id]["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    del _api_keys[key_id]
    await audit_log(current_user.id, "api_key_revoke", "api_key", {"key_id": key_id}, None, True)

    return {"message": "API key revoked"}


# ============================================================
# Session Management
# ============================================================

@router.get("/sessions")
async def list_sessions(current_user: UserInDB = Depends(get_current_active_user)):
    """List active sessions for user."""
    sessions = []
    for token, data in _user_sessions.items():
        if data["user_id"] == current_user.id:
            sessions.append({
                "token_preview": f"{token[:8]}...",
                "created_at": data["created_at"].isoformat(),
                "is_current": False  # Could compare with current token
            })
    return {"sessions": sessions}


@router.delete("/sessions/{token_preview}")
async def revoke_session(
    token_preview: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Revoke a specific session."""
    for token, data in list(_user_sessions.items()):
        if data["user_id"] == current_user.id and token.startswith(token_preview):
            del _user_sessions[token]
            await audit_log(current_user.id, "session_revoke", "session", {"preview": token_preview}, None, True)
            return {"message": "Session revoked"}

    raise HTTPException(status_code=404, detail="Session not found")


# ============================================================
# Health Check
# ============================================================

@router.get("/health")
async def auth_health():
    """Auth service health check."""
    return {
        "status": "healthy",
        "users": len(_user_history),
        "active_sessions": len(_user_sessions),
        "history_entries": sum(len(h) for h in _user_history.values())
    }