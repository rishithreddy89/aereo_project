from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import certificate_service
from app.models.certificate import CertStatus
from app.utils.storage import safe_resolve

router = APIRouter(tags=["certificates"])


@router.get("/certificates/{certificate_id}/download")
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    cert = certificate_service.get_certificate(db, certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.status != CertStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Certificate not yet generated")

    file_path = safe_resolve(certificate_id)
    if file_path is None or not file_path.exists():
        raise HTTPException(status_code=404, detail="Certificate file not found")

    filename = f"certificate_{cert.certificate_number}.pdf"
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename,
    )
