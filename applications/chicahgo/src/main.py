from typing import List

from fastapi import FastAPI
from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from processor import HouseProcessor
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware
import pprint
from models import House, ProcessHouseRequest
from house_service import HouseService
import os

db_host = os.environ['POSTGRES_HOST']
db_user = os.environ['POSTGRES_USER']
db_pass = os.environ['POSTGRES_PASS']
db_port = os.environ['POSTGRES_PORT']
db_db = os.environ['POSTGRES_DB']


print(f"Creating async engine for postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_db}")
async_engine = create_async_engine(
    f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_db}",
    echo=True,
    future=True,
)

house_service = HouseService(async_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Creating sync engine for postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_db}")

    engine = create_engine(
        f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_db}", echo=True, future=True
    )

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    #await ingester.ingest_datasets()

    processor = HouseProcessor(async_engine)
    await processor.initialize()
#   house = await processor.process("1508 N Karlov Ave, Chicago, IL 60651")
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/houses/{house_id}", tags=["houses"])
async def get_house(house_id: str) -> House:
    return await house_service.get_house(house_id)


@app.get("/houses", tags=["houses"])
async def get_houses() -> List[House]:
    return await house_service.get_houses()


@app.post("/houses", tags=["houses"])
async def process_house(house_process_request: ProcessHouseRequest) -> House:
    return await house_service.process_house(house_process_request.address)


# @app.post("/ingest", tags=["tasks"])
# async def ingest():
#     await ingester.ingest_datasets()
#     return {"message": "OK"}
