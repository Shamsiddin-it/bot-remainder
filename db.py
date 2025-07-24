from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL


engine = create_async_engine(DATABASE_URL)
Base = declarative_base()

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

from sqlalchemy import Column, String, Integer, BigInteger

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    description = Column(String)
    remaining_time = Column(String)
    tg_id = Column(BigInteger)

