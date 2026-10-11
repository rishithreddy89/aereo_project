"""
Certificate Worker
==================
Run as a separate process:  python -m app.workers.certificate_worker

Polls MySQL for PENDING jobs, locks one at a time with SELECT ... FOR UPDATE,
generates PDFs, and updates statuses.

Limitations:
- If the worker crashes mid-job, that job stays PROCESSING.
  On restart, the worker calls _recover_stale_jobs() to reset them to PENDING.
- Only one worker process is safe to run at a time per DB (row-level locking
  prevents double-processing, but multiple workers are not tested).
"""

import time
import uuid
import logging
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.certificate_job import CertificateJob, JobStatus
from app.models.certificate import Certificate, CertStatus
from app.services.pdf_generator import generate_certificate_pdf
from app.utils.storage import build_file_path
from app.core.config import settings

logger = logging.getLogger("worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def _recover_stale_jobs(db: Session) -> None:
    """Reset PROCESSING jobs to PENDING on startup (handles crashed workers)."""
    stale = db.scalars(
        select(CertificateJob).where(CertificateJob.status == JobStatus.PROCESSING)
    ).all()
    for job in stale:
        logger.warning("Recovering stale job %s -> PENDING", job.id)
        job.status = JobStatus.PENDING
        job.started_at = None
        for cert in job.certificates:
            if cert.status == CertStatus.PROCESSING:
                cert.status = CertStatus.PENDING
    db.commit()


def _claim_next_job(db: Session) -> CertificateJob | None:
    """
    Atomically claim one PENDING job using SELECT FOR UPDATE.
    Returns the job with status=PROCESSING, or None if nothing is queued.
    """
    job = db.scalars(
        select(CertificateJob)
        .where(CertificateJob.status == JobStatus.PENDING)
        .order_by(CertificateJob.created_at)
        .limit(1)
        .with_for_update(skip_locked=True)
    ).first()

    if not job:
        return None

    job.status = JobStatus.PROCESSING
    job.started_at = datetime.utcnow()
    db.commit()
    return job


def _generate_one(db: Session, cert_id: str, job_id: str) -> None:
    """
    Generate a single certificate PDF.
    Uses a nested transaction (SAVEPOINT) for the failure path so that
    a PDF error does not roll back the outer session (important in tests).
    """
    job = db.get(CertificateJob, job_id)
    cert = db.get(Certificate, cert_id)

    # Mark PROCESSING
    db.execute(update(Certificate).where(Certificate.id == cert_id).values(status=CertStatus.PROCESSING))
    db.commit()

    cert_number = f"CERT-{uuid.uuid4().hex[:10].upper()}"
    file_path = build_file_path(cert_id)

    # Use a savepoint so a failure only rolls back this one certificate
    sp = db.begin_nested()
    try:
        generate_certificate_pdf(
            file_path=file_path,
            certificate_number=cert_number,
            recipient_name=cert.recipient_name,
            event_name=job.event_name,
            certificate_title=job.certificate_title,
            description=job.description,
            issue_date=job.issue_date,
        )
        db.execute(
            update(Certificate).where(Certificate.id == cert_id).values(
                status=CertStatus.COMPLETED,
                certificate_number=cert_number,
                file_path=str(file_path),
                completed_at=datetime.utcnow(),
            )
        )
        db.execute(
            update(CertificateJob).where(CertificateJob.id == job_id).values(
                success_count=CertificateJob.success_count + 1
            )
        )
        sp.commit()
        db.commit()
        logger.info("Generated certificate %s for cert_id=%s", cert_number, cert_id)

    except Exception as exc:
        sp.rollback()  # Only rolls back to the savepoint, outer transaction survives
        db.execute(
            update(Certificate).where(Certificate.id == cert_id).values(
                status=CertStatus.FAILED,
                error_message=str(exc)[:1000],
                completed_at=datetime.utcnow(),
            )
        )
        db.execute(
            update(CertificateJob).where(CertificateJob.id == job_id).values(
                failure_count=CertificateJob.failure_count + 1
            )
        )
        db.commit()
        logger.error("Failed certificate cert_id=%s: %s", cert_id, exc)


def _process_job(db: Session, job: CertificateJob) -> None:
    job_id = job.id
    cert_ids = list(db.scalars(
        select(Certificate.id)
        .where(Certificate.job_id == job_id, Certificate.status == CertStatus.PENDING)
    ).all())

    for cert_id in cert_ids:
        _generate_one(db, cert_id, job_id)

    # Re-fetch counts for final status decision
    row = db.execute(
        select(CertificateJob.success_count, CertificateJob.failure_count)
        .where(CertificateJob.id == job_id)
    ).one()
    success, failure = row.success_count, row.failure_count

    if failure == 0:
        final_status = JobStatus.COMPLETED
    elif success == 0:
        final_status = JobStatus.FAILED
    else:
        final_status = JobStatus.COMPLETED_WITH_ERRORS

    db.execute(
        update(CertificateJob).where(CertificateJob.id == job_id).values(
            status=final_status,
            completed_at=datetime.utcnow(),
        )
    )
    db.commit()
    logger.info("Job %s finished with status %s", job_id, final_status)


def run_worker() -> None:
    logger.info("Worker starting...")
    with SessionLocal() as db:
        _recover_stale_jobs(db)

    while True:
        with SessionLocal() as db:
            try:
                job = _claim_next_job(db)
                if job:
                    logger.info("Processing job %s (%d recipients)", job.id, job.total_count)
                    _process_job(db, job)
                else:
                    time.sleep(settings.WORKER_POLL_INTERVAL)
            except Exception as exc:
                logger.exception("Unexpected worker error: %s", exc)
                db.rollback()
                time.sleep(settings.WORKER_POLL_INTERVAL)


if __name__ == "__main__":
    run_worker()
