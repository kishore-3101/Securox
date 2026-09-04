import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from traffic_core.config import settings

database_url = settings.DATABASE_URL

if database_url.startswith("sqlite"):
    engine = create_engine(
        database_url, 
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
