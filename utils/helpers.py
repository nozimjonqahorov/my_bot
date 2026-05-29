from config import DB_PATH
from db import AsyncSessionLocal, User
from sqlalchemy import select

async def get_user_role(telegram_id: int) -> str:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            return user.role
        # If user not in DB, create as student
        new_user = User(telegram_id=telegram_id, role="student")
        session.add(new_user)
        await session.commit()
        return "student"
