"""
Seed default roles: STUDENT, INSTRUCTOR, ADMIN
Run: python scripts/seed_roles.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from prisma import Prisma, Json

DEFAULT_ROLES = [
    {
        "name": "STUDENT",
        "description": "Student role with basic access",
        "permissions": Json(["read:courses", "submit:assignments", "view:feedback"]),
    },
    {
        "name": "INSTRUCTOR",
        "description": "Instructor role with teaching capabilities",
        "permissions": Json([
            "read:courses",
            "write:courses",
            "read:students",
            "write:feedback",
            "read:analytics",
        ]),
    },
    {
        "name": "ADMIN",
        "description": "Administrator with full system access",
        "permissions": Json(["*"]),
    },
]


async def seed_roles():
    prisma = Prisma()
    await prisma.connect()

    for role_data in DEFAULT_ROLES:
        existing = await prisma.role.find_unique(where={"name": role_data["name"]})
        if existing:
            print(f"Role '{role_data['name']}' already exists, skipping")
            continue

        role = await prisma.role.create(data=role_data)
        print(f"Created role: {role.name} ({role.id})")

    await prisma.disconnect()


if __name__ == "__main__":
    asyncio.run(seed_roles())
