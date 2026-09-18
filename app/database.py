"""
Database connection using Prisma ORM
"""
from prisma import Prisma

# Global Prisma client instance
prisma = Prisma()


async def get_db():
    """Dependency for database access"""
    if not prisma.is_connected():
        await prisma.connect()
    return prisma
