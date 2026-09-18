"""
Authentication Routes
Handles user authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.controllers.auth_controller import AuthController
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefresh,
)

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    return await AuthController.get_current_user(token)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    return await AuthController.register(user_data)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login and get access tokens"""
    return await AuthController.login(credentials)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token using refresh token"""
    return await AuthController.refresh_access_token(token_data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(token_data: TokenRefresh):
    """
    Logout by revoking refresh token

    - blacklist=True (default): Token is blacklisted (web frontend)
    - blacklist=False: Token is NOT blacklisted (desktop apps with auto-restore)
    """
    await AuthController.logout(
        token_data.refresh_token,
        blacklist=token_data.blacklist
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information"""
    return current_user
