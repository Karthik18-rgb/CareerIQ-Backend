"""
Authentication service: registration, login, token management.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.exceptions import UnauthorizedException, ConflictException
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    UserRegisterResponse,
    UserLoginResponse,
    TokenResponse,
)


def _user_to_response(user: User) -> UserResponse:
    """Convert User ORM object to UserResponse schema."""
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _create_access_token(user_id: str) -> str:
    """Create a short-lived JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "type": "access", "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _create_refresh_token(user_id: str) -> str:
    """Create a long-lived JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {"sub": str(user_id), "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _create_token_pair(user_id: str) -> TokenResponse:
    """Create both access and refresh tokens."""
    return TokenResponse(
        access_token=_create_access_token(user_id),
        refresh_token=_create_refresh_token(user_id),
        token_type="bearer",
    )


def register_user(db: Session, request: UserRegisterRequest) -> UserRegisterResponse:
    """Register a new user."""
    if db.query(User).filter(User.email == request.email).first():
        raise ConflictException("An account with this email already exists")

    if db.query(User).filter(User.username == request.username).first():
        raise ConflictException("This username is already taken")

    user = User(
        email=request.email,
        username=request.username,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    tokens = _create_token_pair(user.id)
    return UserRegisterResponse(
        message="User registered successfully",
        user=_user_to_response(user),
        tokens=tokens,
    )


def login_user(db: Session, request: UserLoginRequest) -> UserLoginResponse:
    """Authenticate a user and return tokens."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise UnauthorizedException("Invalid email or password")

    if not verify_password(request.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated. Contact support.")

    tokens = _create_token_pair(user.id)
    return UserLoginResponse(
        message="Login successful",
        user=_user_to_response(user),
        tokens=tokens,
    )


def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse:
    """Issue a new access token using a valid refresh token."""
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")
        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("Invalid token payload")
    except JWTError:
        raise UnauthorizedException("Invalid or expired refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    return _create_token_pair(user.id)


def get_current_user(db: Session, token: str) -> User:
    """Decode an access token and return the authenticated user."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            raise UnauthorizedException("Invalid token type")
        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("Invalid token payload")
    except JWTError:
        raise UnauthorizedException("Invalid or expired access token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedException("User not found")
    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    return user
