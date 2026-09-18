"""
Authentication Controller
Handles user authentication, registration, and token management
"""
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.database import prisma
from app.config import settings
from app.schemas.auth import UserCreate, UserLogin, TokenResponse, UserResponse
from app.controllers.role_controller import role_to_response
from app.redis_client import blacklist_refresh_token, is_refresh_token_blacklisted

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthController:
    """Authentication business logic"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def register(user_data: UserCreate) -> TokenResponse:
        """Register new user"""
        # Check if user exists
        existing_user = await prisma.user.find_unique(where={"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email đã tồn tại"
            )

        # Hash password
        hashed_password = AuthController.get_password_hash(user_data.password)

        # Get role_id - default to STUDENT role if not provided
        role_id = user_data.role_id
        if not role_id:
            default_role = await prisma.role.find_unique(where={"name": "STUDENT"})
            if not default_role:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Default STUDENT role not found in database"
                )
            role_id = default_role.id

        # Verify role exists
        role = await prisma.role.find_unique(where={"id": role_id})
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role_id"
            )

        # Create user
        user = await prisma.user.create(
            data={
                "email": user_data.email,
                "password": hashed_password,
                "name": user_data.name,
                "roleId": role_id,
            }
        )

        # If student role, create student profile
        if role.name == "STUDENT":
            await prisma.student.create(
                data={
                    "userId": user.id,
                    "studentId": f"STU{user.id[:8].upper()}",
                }
            )

        # Generate tokens
        access_token = AuthController.create_access_token(data={"sub": user.id})
        refresh_token = AuthController.create_refresh_token(data={"sub": user.id})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    @staticmethod
    async def login(credentials: UserLogin) -> TokenResponse:
        """Authenticate user and return tokens"""
        # Find user
        user = await prisma.user.find_unique(where={"email": credentials.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tài khoản hoặc mật khẩu không chính xác"
            )

        # Verify password
        if not AuthController.verify_password(credentials.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tài khoản hoặc mật khẩu không chính xác"
            )

        # Check if user is active
        if not user.isActive:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản đã bị vô hiệu hóa"
            )

        # Generate tokens
        access_token = AuthController.create_access_token(data={"sub": user.id})
        refresh_token = AuthController.create_refresh_token(data={"sub": user.id})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Check if token is blacklisted
        if await is_refresh_token_blacklisted(refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )

        # Verify user exists
        user = await prisma.user.find_unique(where={"id": user_id})
        if not user or not user.isActive:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Generate new tokens
        new_access_token = AuthController.create_access_token(data={"sub": user_id})
        new_refresh_token = AuthController.create_refresh_token(data={"sub": user_id})

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )

    @staticmethod
    async def logout(refresh_token: str, blacklist: bool = True) -> None:
        """
        Logout by optionally blacklisting the refresh token

        Args:
            refresh_token: The refresh token to revoke
            blacklist: If True, add token to blacklist. If False, just acknowledge logout.
                      Default True for backward compatibility with web frontend.
        """
        if not blacklist:
            # Desktop app logout - don't blacklist token for auto-restore
            return

        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            token_type: str = payload.get("type")
            exp: int = payload.get("exp")

            if token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )

            # Calculate remaining TTL until token's natural expiry
            now = datetime.now(timezone.utc).timestamp()
            ttl = int(exp - now)

            if ttl > 0:
                await blacklist_refresh_token(refresh_token, ttl)
        except JWTError:
            # Token already invalid/expired, silently succeed
            pass

    @staticmethod
    async def get_current_user(token: str) -> UserResponse:
        """Get current user from JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

        user = await prisma.user.find_unique(
            where={"id": user_id},
            include={"role": True}
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role_id=user.roleId,
            role=role_to_response(user.role) if user.role else None,
            avatar=user.avatar,
            is_active=user.isActive,
            created_at=user.createdAt,
        )
