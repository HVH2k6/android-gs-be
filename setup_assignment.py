from app.database import prisma
import asyncio

async def setup_test_data():
    await prisma.connect()

    course = await prisma.course.find_first()
    if not course:
        print('Creating test course...')
        course = await prisma.course.create(data={
            'code': 'ANDROID101',
            'title': 'Android Development',
            'description': 'Learn Android app development',
        })
        print(f'Created course: {course.id}')
    else:
        print(f'Using existing course: {course.id}')

    existing = await prisma.assignment.find_first(
        where={'courseId': course.id, 'order': 0}
    )
    if existing:
        print(f'Assignment order=0 already exists: {existing.id}')
        assignment = existing
    else:
        print('Creating assignment order=0...')
        assignment = await prisma.assignment.create(data={
            'courseId': course.id,
            'order': 0,
            'title': 'Default Assignment for Desktop App',
            'description': 'Auto-created assignment for desktop app testing',
            'isPublished': True,
        })
        print(f'Created assignment: {assignment.id}')

    print(f'\n=== Use this assignment_id ===')
    print(f'ID: {assignment.id}')
    print(f'Title: {assignment.title}')

    await prisma.disconnect()

if __name__ == '__main__':
    asyncio.run(setup_test_data())
