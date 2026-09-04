"""
CAREGUARD — Main FastAPI Application Entrypoint
Healthcare Cybersecurity Intelligence Platform built from scratch.
Zero Synthetic Data Policy.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from healthcare_core.core.config import settings
from healthcare_core.api.endpoints import router as api_router
from healthcare_core.data.loaders.mimic_ed_loader import mimic_ed_loader
from healthcare_core.data.loaders.mimic_clinical_loader import mimic_clinical_loader
from healthcare_core.data.loaders.eicu_loader import eicu_loader
from healthcare_core.data.loaders.onc_loader import onc_loader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("careguard.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CAREGUARD Healthcare Cybersecurity Platform...")
    logger.info("Zero Synthetic Data Policy: Active. Verifying organic datasets...")
    # Pre-warm organic loaders
    try:
        mimic_ed_loader.load()
        mimic_clinical_loader.load()
        eicu_loader.load()
        onc_loader.load()
        logger.info("Organic healthcare datasets successfully loaded and ready.")
    except Exception as e:
        logger.error(f"Error during dataset pre-warming: {e}")
    yield
    logger.info("Shutting down CAREGUARD platform.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Institutional-grade Healthcare Cybersecurity Intelligence Platform connecting cyber threats to clinical care workflows.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "domain": "HEALTHCARE_CYBERSECURITY",
        "data_policy": "ZERO_SYNTHETIC_DATA — 100% Organic Data Only",
        "docs_url": "/docs"
    }

@app.get("/health")
def root_health():
    return {"status": "UP", "service": settings.PROJECT_NAME, "healthy": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

