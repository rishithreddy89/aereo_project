import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.certificate_job import CertificateJob, JobStatus
from app.models.certificate import Certificate, CertStatus
from app.schemas.certificate_job import CertificateJobCreate


def create_job(db: Session, payload: CertificateJobCreate) -> CertificateJob:
    job = CertificateJob(
        id=str(uuid.uuid4()),
        event_name=payload.event_name,
        certificate_title=payload.certificate_title,
        description=payload.description,
        issue_date=str(payload.issue_date),
        status=JobStatus.PENDING,
        total_count=len(payload.recipients),
        success_count=0,
        failure_count=0,
        created_at=datetime.utcnow(),
    )
    db.add(job)
    db.flush()

    for recipient in payload.recipients:
        cert = Certificate(
            id=str(uuid.uuid4()),
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=str(recipient.email),
            status=CertStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        db.add(cert)

    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> CertificateJob | None:
    return db.get(CertificateJob, job_id)
