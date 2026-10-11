import os
import uuid
from pathlib import Path
from app.core.config import settings


def get_storage_dir() -> Path:
    path = Path(settings.STORAGE_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_file_path(certificate_id: str) -> Path:
    return get_storage_dir() / f"{certificate_id}.pdf"


def safe_resolve(certificate_id: str) -> Path | None:
    """Return the absolute path only if it lives inside STORAGE_DIR."""
    storage = get_storage_dir().resolve()
    candidate = (storage / f"{certificate_id}.pdf").resolve()
    if not str(candidate).startswith(str(storage)):
        return None
    return candidate
