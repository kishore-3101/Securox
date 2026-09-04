import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, ConfigDict

class Settings(BaseModel):
    model_config = ConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "CAREGUARD — Cyber-to-Care Healthcare Security Intelligence"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Absolute path to organic datasets folder
    @staticmethod
    def _resolve_datasets_dir() -> str:
        env_val = os.getenv("HEALTHCARE_DATASETS_DIR") or os.getenv("DATASETS_DIR")
        if env_val and os.path.exists(env_val):
            return str(Path(env_val).resolve())
        candidates = [
            Path(r"C:\Users\praja\Downloads\Healthcare\datasets"),
            Path(__file__).resolve().parent.parent.parent.parent / "datasets",
            Path(__file__).resolve().parent.parent.parent / "datasets",
            Path(r"D:\HC\Healthcare\datasets"),
            Path(r"D:\Smart Horizon\Healthcare\datasets")
        ]
        for c in candidates:
            if c.exists():
                return str(c.resolve())
        return str(candidates[0])

    DATASETS_DIR: str = _resolve_datasets_dir()

    # Path to cyberdatasets directory (auto-resolves local relative or dedicated directory)
    @staticmethod
    def _resolve_cyberdatasets_dir() -> str:
        env_val = os.getenv("CYBERDATASETS_DIR")
        if env_val and os.path.exists(env_val):
            return str(Path(env_val).resolve())
        candidates = [
            Path(r"C:\Users\praja\Downloads\Healthcare\cyberdatasets"),
            Path(__file__).resolve().parent.parent.parent / "cyberdatasets",
            Path(__file__).resolve().parent.parent.parent.parent / "cyberdatasets",
            Path(r"D:\HC\Healthcare\cyberdatasets"),
            Path(r"D:\Smart Horizon\Healthcare\cyberdatasets")
        ]
        for c in candidates:
            if c.exists():
                return str(c.resolve())
        return str(candidates[0])

    CYBERDATASETS_DIR: str = _resolve_cyberdatasets_dir()
    
    # CORS Configuration — Explicit Local and Staging Frontend Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Zero Synthetic Data Policy Flag
    ZERO_SYNTHETIC_DATA: bool = True

settings = Settings()

