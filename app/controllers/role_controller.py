"""
Role Controller
Handles role management operations
"""
from fastapi import HTTPException, status
from typing import List, Optional

from prisma import Json

from app.database import prisma
from app.schemas.auth import RoleCreate, RoleUpdate, RoleResponse


def role_to_response(role) -> RoleResponse:
    """Convert Prisma Role model to RoleResponse schema"""
    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=role.permissions,
        created_at=role.createdAt,
        updated_at=role.updatedAt,
    )


class RoleController:
    """Role management business logic"""

    @staticmethod
    async def create_role(role_data: RoleCreate) -> RoleResponse:
        """Create a new role"""
        # Check if role name already exists
        existing_role = await prisma.role.find_unique(where={"name": role_data.name})
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_data.name}' already exists"
            )

        # Create role
        role = await prisma.role.create(
            data={
                "name": role_data.name,
                "description": role_data.description,
                "permissions": Json(role_data.permissions),
            }
        )

        return role_to_response(role)

    @staticmethod
    async def get_role(role_id: str) -> RoleResponse:
        """Get role by ID"""
        role = await prisma.role.find_unique(where={"id": role_id})
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

        return role_to_response(role)

    @staticmethod
    async def get_role_by_name(name: str) -> RoleResponse:
        """Get role by name"""
        role = await prisma.role.find_unique(where={"name": name})
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{name}' not found"
            )

        return role_to_response(role)

    @staticmethod
    async def list_roles() -> List[RoleResponse]:
        """List all roles"""
        roles = await prisma.role.find_many(order={"name": "asc"})
        return [role_to_response(role) for role in roles]

    @staticmethod
    async def update_role(role_id: str, role_data: RoleUpdate) -> RoleResponse:
        """Update role"""
        # Check if role exists
        existing_role = await prisma.role.find_unique(where={"id": role_id})
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

        # Prepare update data
        update_data = {}
        if role_data.description is not None:
            update_data["description"] = role_data.description
        if role_data.permissions is not None:
            update_data["permissions"] = Json(role_data.permissions)

        # Update role
        role = await prisma.role.update(
            where={"id": role_id},
            data=update_data
        )

        return role_to_response(role)

    @staticmethod
    async def delete_role(role_id: str) -> dict:
        """Delete role (only if no users assigned)"""
        # Check if role exists
        role = await prisma.role.find_unique(
            where={"id": role_id},
            include={"users": True}
        )
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

        # Check if role has users
        if role.users and len(role.users) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete role. {len(role.users)} user(s) are assigned to this role"
            )

        # Delete role
        await prisma.role.delete(where={"id": role_id})

        return {"message": "Role deleted successfully"}
