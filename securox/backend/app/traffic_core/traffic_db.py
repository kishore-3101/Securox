"""
Securox Traffic Module — Authoritative Database Integration
Binds traffic routes directly to the central unified SQLAlchemy persistence engine.
"""

from core.database import engine, SessionLocal, Base, get_db

__all__ = ["engine", "SessionLocal", "Base", "get_db"]
