"""
Securox — Unified Authoritative Persistence Engine
Standardized on SQLAlchemy 2.0 with production PostgreSQL and local SQLite WAL support.
"""

import os
import logging
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session, DeclarativeBase
from sqlalchemy.engine import Engine

logger = logging.getLogger("securox.database")

# Authoritative database path for SQLite
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DB_FILE = Path(__file__).resolve().parent / "securox.db"
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_FILE}"

DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("SECUROX_DATABASE_URL", DEFAULT_DB_URL))

# Ensure parent directory exists for SQLite
if DATABASE_URL.startswith("sqlite"):
    db_file_str = DATABASE_URL.replace("sqlite:///", "")
    if db_file_str and not db_file_str.startswith(":memory:"):
        Path(db_file_str).parent.mkdir(parents=True, exist_ok=True)

# SQLAlchemy 2.0 Engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()

    logger.info(f"Initialized SQLite persistence engine (WAL mode) at {DATABASE_URL}")
else:
    # PostgreSQL / production dialect
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        pool_timeout=float(os.getenv("DB_POOL_TIMEOUT", "30.0")),
        echo=False,
    )
    logger.info(f"Initialized PostgreSQL production persistence engine at {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'target host'}")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Authoritative SQLAlchemy 2.0 DeclarativeBase."""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding transactional database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes schema tables and indexes."""
    from . import models  # Ensure all models are registered
    Base.metadata.create_all(bind=engine)
    logger.info("Unified schema tables verified/created successfully.")
