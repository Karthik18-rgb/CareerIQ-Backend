"""
Authentication API router.
"""

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.auth.service import (
    register_user,
    login_user,
    refresh_access_token,
    get_current_user,
)
from app.core.exceptions import UnauthorizedException
from app.database.connection import get_db
from app.schemas.auth import (
    UserLoginRequest,
    UserLoginResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    UserResponse,
    UserUpdateRequest,
    TokenRefreshRequest,
    TokenResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRegisterResponse, status_code=201)
def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user account."""
    return register_user(db=db, request=request)


@router.post("/login", response_model=UserLoginResponse)
def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate user and return JWT tokens."""
    return login_user(db=db, request=request)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: TokenRefreshRequest,
    db: Session = Depends(get_db),
):
    """Refresh an expired access token using a refresh token."""
    return refresh_access_token(db=db, refresh_token=request.refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(
    authorization: str = Header(..., description="Bearer <access_token>"),
    db: Session = Depends(get_db),
):
    """Return the currently authenticated user's profile."""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedException("Invalid authorization header format")

    user = get_current_user(db=db, token=token)
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


@router.put("/profile", response_model=UserResponse)
def update_profile(
    request: UserUpdateRequest,
    authorization: str = Header(..., description="Bearer <access_token>"),
    db: Session = Depends(get_db),
):
    """Update the authenticated user's profile (full_name, username)."""
    from app.core.exceptions import ConflictException
    from app.models.user import User

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedException("Invalid authorization header format")

    user = get_current_user(db=db, token=token)

    if request.full_name is not None:
        user.full_name = request.full_name
    if request.username is not None:
        existing = db.query(User).filter(
            User.username == request.username, User.id != user.id
        ).first()
        if existing:
            raise ConflictException("This username is already taken")
        user.username = request.username

    db.commit()
    db.refresh(user)

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
