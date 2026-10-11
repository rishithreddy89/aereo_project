"""
Tests for partial failure: one certificate fails, job continues and ends
with COMPLETED_WITH_ERRORS.
"""
import uuid
import tempfile
from unittest.mock import patch
from pathlib import Path
from datetime import datetime

from app.models.certificate_job import CertificateJob, JobStatus
from app.models.certificate import Certificate, CertStatus
from app.workers.certificate_worker import _process_job


def _make_job(db, recipients):
    job = CertificateJob(
        id=str(uuid.uuid4()),
        event_name="Test Event",
        certificate_title="Test Cert",
        description="Test Desc",
        issue_date="2026-10-11",
        status=JobStatus.PROCESSING,
        total_count=len(recipients),
        success_count=0,
        failure_count=0,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
    )
    db.add(job)
    db.flush()
    for name, email in recipients:
        cert = Certificate(
            id=str(uuid.uuid4()),
            job_id=job.id,
            recipient_name=name,
            recipient_email=email,
            status=CertStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        db.add(cert)
    db.commit()
    db.refresh(job)
    return job


def test_partial_failure_continues_remaining(db):
    """If one PDF fails, the other still completes."""
    job = _make_job(db, [("Alice", "alice@example.com"), ("Bob", "bob@example.com")])

    call_count = {"n": 0}

    def fake_generate(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("Simulated PDF failure")
        # Write a minimal valid file for the second call
        kwargs["file_path"].write_bytes(b"%PDF-1.4 fake")

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("app.workers.certificate_worker.build_file_path") as mock_path, \
             patch("app.workers.certificate_worker.generate_certificate_pdf", side_effect=fake_generate):
            mock_path.side_effect = lambda cert_id: Path(tmpdir) / f"{cert_id}.pdf"
            _process_job(db, job)

    db.refresh(job)
    assert job.status == JobStatus.COMPLETED_WITH_ERRORS
    assert job.success_count == 1
    assert job.failure_count == 1


def test_all_fail_sets_failed_status(db):
    job = _make_job(db, [("Alice", "alice@example.com")])

    def always_fail(**kwargs):
        raise RuntimeError("Always fails")

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("app.workers.certificate_worker.build_file_path") as mock_path, \
             patch("app.workers.certificate_worker.generate_certificate_pdf", side_effect=always_fail):
            mock_path.side_effect = lambda cert_id: Path(tmpdir) / f"{cert_id}.pdf"
            _process_job(db, job)

    db.refresh(job)
    assert job.status == JobStatus.FAILED
    assert job.failure_count == 1
    assert job.success_count == 0


def test_all_succeed_sets_completed_status(db):
    job = _make_job(db, [("Alice", "alice@example.com")])

    def fake_generate(**kwargs):
        kwargs["file_path"].write_bytes(b"%PDF-1.4 fake")

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("app.workers.certificate_worker.build_file_path") as mock_path, \
             patch("app.workers.certificate_worker.generate_certificate_pdf", side_effect=fake_generate):
            mock_path.side_effect = lambda cert_id: Path(tmpdir) / f"{cert_id}.pdf"
            _process_job(db, job)

    db.refresh(job)
    assert job.status == JobStatus.COMPLETED
    assert job.success_count == 1
    assert job.failure_count == 0
