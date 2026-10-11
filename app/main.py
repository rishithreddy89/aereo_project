from fastapi import FastAPI
from app.core.logging import setup_logging
from app.api.routes import health, certificate_jobs, certificates

setup_logging()

app = FastAPI(title="Bulk Certificate Generator", version="1.0.0")

app.include_router(health.router)
app.include_router(certificate_jobs.router, prefix="/api/v1")
app.include_router(certificates.router, prefix="/api/v1")
