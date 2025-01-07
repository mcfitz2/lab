import logging
from typing import List

from fastapi import FastAPI, Request, Response
from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from processor import HouseProcessor
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware
import pprint
from models import House, ProcessHouseRequest
from house_service import HouseService
import os
from starlette.background import BackgroundTask

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
        f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_db}", echo=True, future=True
    )

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    #await ingester.ingest_datasets()

    processor = HouseProcessor(async_engine)
    await processor.initialize()
#   house = await processor.process("1508 N Karlov Ave, Chicago, IL 60651")
    yield

def log_info(req_body):
    logging.info(req_body)

app = FastAPI(lifespan=lifespan)

@app.middleware('http')
async def some_middleware(request: Request, call_next):
    req_body = await request.body()
    #await set_body(request, req_body)  # not needed when using FastAPI>=0.108.0.
    
    
    
    
    task = BackgroundTask(log_info, req_body)
    response = await call_next(request)
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    res_body = b''.join(chunks)
    return Response(content=res_body, status_code=response.status_code, 
        headers=dict(response.headers), media_type=response.media_type, background=task)
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
