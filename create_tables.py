import asyncio

from app.database import Base, engine
from app import models


async def main():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


asyncio.run(main())