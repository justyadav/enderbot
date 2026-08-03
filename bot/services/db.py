"""Async SQLAlchemy DB service with a GuildConfig model.
Uses sqlite+aiosqlite by default when DATABASE_URL is not provided.
"""
import os
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, BigInteger, Boolean, Float, Integer, JSON

Base = declarative_base()

class GuildConfig(Base):
    __tablename__ = "guild_config"
    guild_id = Column(BigInteger, primary_key=True)
    automod_enabled = Column(Boolean, default=True, nullable=False)
    anti_invite = Column(Boolean, default=True, nullable=False)
    anti_link = Column(Boolean, default=False, nullable=False)
    anti_mention_spam = Column(Boolean, default=True, nullable=False)
    anti_emoji_spam = Column(Boolean, default=True, nullable=False)
    caps_threshold = Column(Float, default=0.75, nullable=False)
    autorole_id = Column(BigInteger, nullable=True)
    logging_channels = Column(JSON, default={})

_engine: Optional[AsyncEngine] = None
_async_session: Optional[sessionmaker] = None

async def init_db(database_url: Optional[str] = None):
    global _engine, _async_session
    database_url = database_url or os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///./data.db"
    _engine = create_async_engine(database_url, future=True)
    _async_session = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    # create tables
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def get_sessionmaker():
    if _async_session is None:
        raise RuntimeError("DB is not initialized. Call init_db first.")
    return _async_session

# convenience context manager
async def get_session() -> AsyncSession:
    Session = get_sessionmaker()
    async with Session() as session:
        yield session

# helper functions
async def get_guild_config(session: AsyncSession, guild_id: int) -> GuildConfig:
    cfg = await session.get(GuildConfig, guild_id)
    if not cfg:
        cfg = GuildConfig(guild_id=guild_id)
        session.add(cfg)
        await session.commit()
        await session.refresh(cfg)
    return cfg

async def upsert_guild_config(session: AsyncSession, guild_id: int, **kwargs) -> GuildConfig:
    cfg = await session.get(GuildConfig, guild_id)
    if not cfg:
        cfg = GuildConfig(guild_id=guild_id, **kwargs)
        session.add(cfg)
    else:
        for k, v in kwargs.items():
            setattr(cfg, k, v)
    await session.commit()
    await session.refresh(cfg)
    return cfg
