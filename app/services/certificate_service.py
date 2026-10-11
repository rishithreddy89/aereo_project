from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.certificate import Certificate, CertStatus


def get_certificates_for_job(db: Session, job_id: str) -> list[Certificate]:
    stmt = select(Certificate).where(Certificate.job_id == job_id)
    return list(db.scalars(stmt).all())


def get_certificate(db: Session, certificate_id: str) -> Certificate | None:
    return db.get(Certificate, certificate_id)
