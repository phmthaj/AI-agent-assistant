import asyncio
from sqlalchemy import text
from app.database import engine

async def main():
    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT current_database(), current_user")
        )
        print(result.fetchone())

asyncio.run(main())