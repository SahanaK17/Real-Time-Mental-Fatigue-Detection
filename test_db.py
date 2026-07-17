
import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models import User, UserRole
from app.core.security import get_password_hash

async def test():
    async with AsyncSessionLocal() as db:
        user = User(email='test5@company.com', username='test5', full_name='Test', hashed_password=get_password_hash('pass'), role=UserRole.EMPLOYEE)
        db.add(user)
        await db.commit()
        print('OK')

asyncio.run(test())

