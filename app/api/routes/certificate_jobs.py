from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.certificate_job import CertificateJobCreate, CertificateJobResponse, CertificateJobStatus
from app.schemas.certificate import CertificateOut
from app.services import job_service, certificate_service
from app.models.certificate import CertStatus

router = APIRouter(tags=["certificate-jobs"])


@router.post("/certificate-jobs", status_code=status.HTTP_202_ACCEPTED, response_model=CertificateJobResponse)
def create_certificate_job(payload: CertificateJobCreate, db: Session = Depends(get_db)):
    job = job_service.create_job(db, payload)
    return CertificateJobResponse(
        job_id=job.id,
        status=job.status,
        message=f"Job accepted. {job.total_count} certificate(s) queued for generation.",
    )


@router.get("/certificate-jobs/{job_id}", response_model=CertificateJobStatus)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    certs = certificate_service.get_certificates_for_job(db, job_id)
    pending = sum(1 for c in certs if c.status == CertStatus.PENDING)
    processing = sum(1 for c in certs if c.status == CertStatus.PROCESSING)

    cert_list = [
        {
            "certificate_id": c.id,
            "recipient_name": c.recipient_name,
            "recipient_email": c.recipient_email,
            "status": c.status,
            "error_message": c.error_message,
        }
        for c in certs
    ]

    return CertificateJobStatus(
        job_id=job.id,
        status=job.status,
        total_count=job.total_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        pending_count=pending,
        processing_count=processing,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        certificates=cert_list,
    )


@router.get("/certificate-jobs/{job_id}/certificates", response_model=list[CertificateOut])
def list_certificates(job_id: str, db: Session = Depends(get_db)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    certs = certificate_service.get_certificates_for_job(db, job_id)
    return [
        CertificateOut(
            certificate_id=c.id,
            recipient_name=c.recipient_name,
            recipient_email=c.recipient_email,
            status=c.status,
            certificate_number=c.certificate_number,
            download_url=f"/api/v1/certificates/{c.id}/download" if c.status == CertStatus.COMPLETED else None,
        )
        for c in certs
    ]
