from models import House
from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from processor import HouseProcessor
import pprint

class HouseService:
    def __init__(self, engine):
        self.engine = engine
        self.processor = HouseProcessor(self.engine)

    async def get_house(self, house_id) -> House:
        async with AsyncSession(self.engine) as session:
            statement = select(House).where(House.house_id == house_id)
            house = await session.exec(statement)
            return house.first()

    async def get_houses(self) -> List[House]:
        async with AsyncSession(self.engine) as session:
            statement = select(House)
            houses = await session.exec(statement)
            return houses.all()

    async def process_house(self, address: str) -> House:
        house = await self.processor.process(address)
        pprint.pprint(house)
        house_id = await self.add_house(house)
        return await self.get_house(house_id)

    async def add_house(self, house: House) -> str:
        async with AsyncSession(self.engine) as session:
            await House.upsert(house, session)
            await session.commit()
            return house.house_id
