from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from core.config import settings


engine = create_engine(
    settings.DATABASE_URL.replace("+asyncpg", ""),
    echo=False,
    future=True,
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


@contextmanager
def get_sync_db() -> Generator[Session, None, None]:
    """Sync dependency for workers."""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()
