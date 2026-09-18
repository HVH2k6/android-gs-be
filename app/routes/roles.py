"""
Role Routes
API endpoints for role management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.controllers.role_controller import RoleController
from app.schemas.auth import RoleCreate, RoleUpdate, RoleResponse, UserResponse
from app.routes.auth import get_current_user

router = APIRouter()


def _require_admin(current_user: UserResponse):
    if not current_user.role or current_user.role.name != "ADMIN":
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new role (Admin only)"""
    _require_admin(current_user)
    return await RoleController.create_role(role_data)


@router.get("/", response_model=List[RoleResponse])
async def list_roles(current_user: UserResponse = Depends(get_current_user)):
    """List all roles"""
    return await RoleController.list_roles()


@router.get("/name/{name}", response_model=RoleResponse)
async def get_role_by_name(
    name: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get role by name"""
    return await RoleController.get_role_by_name(name)


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get role by ID"""
    return await RoleController.get_role(role_id)


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update role (Admin only)"""
    _require_admin(current_user)
    return await RoleController.update_role(role_id, role_data)


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete role (Admin only, only if no users assigned)"""
    _require_admin(current_user)
    return await RoleController.delete_role(role_id)
