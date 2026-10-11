"""Tests for certificate download endpoint."""
import uuid
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from app.models.certificate_job import CertificateJob, JobStatus
from app.models.certificate import Certificate, CertStatus


def _seed_completed_cert(db, tmpdir: str):
    job = CertificateJob(
        id=str(uuid.uuid4()),
        event_name="Workshop",
        certificate_title="Certificate",
        description="Desc",
        issue_date="2026-10-11",
        status=JobStatus.COMPLETED,
        total_count=1,
        success_count=1,
        failure_count=0,
        created_at=datetime.utcnow(),
    )
    db.add(job)
    db.flush()

    cert_id = str(uuid.uuid4())
    pdf_path = Path(tmpdir) / f"{cert_id}.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake content")

    cert = Certificate(
        id=cert_id,
        job_id=job.id,
        recipient_name="Alice",
        recipient_email="alice@example.com",
        status=CertStatus.COMPLETED,
        certificate_number="CERT-DOWNLOAD01",
        file_path=str(pdf_path),
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    db.add(cert)
    db.commit()
    return cert


def test_download_returns_pdf(client, db):
    with tempfile.TemporaryDirectory() as tmpdir:
        cert = _seed_completed_cert(db, tmpdir)
        with patch("app.api.routes.certificates.safe_resolve") as mock_resolve:
            mock_resolve.return_value = Path(cert.file_path)
            resp = client.get(f"/api/v1/certificates/{cert.id}/download")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"


def test_download_unknown_cert_returns_404(client):
    resp = client.get("/api/v1/certificates/nonexistent-id/download")
    assert resp.status_code == 404


def test_download_pending_cert_returns_404(client, db):
    job = CertificateJob(
        id=str(uuid.uuid4()),
        event_name="Workshop",
        certificate_title="Certificate",
        description="Desc",
        issue_date="2026-10-11",
        status=JobStatus.PENDING,
        total_count=1,
        success_count=0,
        failure_count=0,
        created_at=datetime.utcnow(),
    )
    db.add(job)
    db.flush()
    cert = Certificate(
        id=str(uuid.uuid4()),
        job_id=job.id,
        recipient_name="Bob",
        recipient_email="bob@example.com",
        status=CertStatus.PENDING,
        created_at=datetime.utcnow(),
    )
    db.add(cert)
    db.commit()

    resp = client.get(f"/api/v1/certificates/{cert.id}/download")
    assert resp.status_code == 404


def test_download_missing_file_returns_404(client, db):
    with tempfile.TemporaryDirectory() as tmpdir:
        cert = _seed_completed_cert(db, tmpdir)
        # Point safe_resolve to a non-existent path
        with patch("app.api.routes.certificates.safe_resolve") as mock_resolve:
            mock_resolve.return_value = Path(tmpdir) / "missing.pdf"
            resp = client.get(f"/api/v1/certificates/{cert.id}/download")
        assert resp.status_code == 404
