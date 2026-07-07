from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
print("DATABASE_URL: ", DATABASE_URL)
# engine is connection pool, created once, reusable across all requests
engine = create_async_engine(
    DATABASE_URL,
    pool_size = 10, #max persistent connection 
    max_overflow = 20 , # extra connection under load
    echo = True
)

#SessionFactory - Creates new AsyncSession objects on demand
AsyncSessionLocal = async_sessionmaker(
    bind= engine,
    expire_on_commit= False
)

# All models inherit from this base
class Base(DeclarativeBase):
    pass

# Lifespan manager - runs on all startup and shutdown
@asynccontextmanager
async def lifespan(app):
    # Startup : creates all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("👍Database Created And Connected successfully")
    yield
    # shutdown - dispose all connections
    await engine.dispose()
    print("🚙DataBase Disconnected")    