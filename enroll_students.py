from app.database import prisma
import asyncio

async def enroll_students():
    await prisma.connect()

    course = await prisma.course.find_first()
    print(f'Course: {course.id} - {course.title}')

    students = await prisma.student.find_many(include={'user': True})
    print(f'\nFound {len(students)} students')

    for student in students:
        existing = await prisma.enrollment.find_first(
            where={'studentId': student.id, 'courseId': course.id}
        )

        if existing:
            print(f'Student {student.user.name} already enrolled')
        else:
            enrollment = await prisma.enrollment.create(data={
                'studentId': student.id,
                'courseId': course.id,
                'status': 'ACTIVE',
            })
            print(f'Enrolled {student.user.name} -> {course.title}')

    await prisma.disconnect()

if __name__ == '__main__':
    asyncio.run(enroll_students())
