import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Settings:
    PROJECT_NAME: str = "SECUROX Traffic & Cyber Command Center"
    VERSION: str = "2.4.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECUROX_SECRET_KEY", "securox-super-secret-command-center-token-key-2026-traffic-soc")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Dual database support: Use PostgreSQL if provided in env, else resilient SQLite
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'traffic.db'}"
    )
    
    # System Telemetry & Simulation intervals
    TELEMETRY_INTERVAL_SEC: float = float(os.getenv("TELEMETRY_INTERVAL_SEC", "2.5"))
    DEMO_MODE: bool = True
    
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "*"
    ]

settings = Settings()
