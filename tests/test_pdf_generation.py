import tempfile
from pathlib import Path
from app.services.pdf_generator import generate_certificate_pdf


def test_pdf_is_created():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test_cert.pdf"
        generate_certificate_pdf(
            file_path=path,
            certificate_number="CERT-TEST001",
            recipient_name="Alice Johnson",
            event_name="Python Workshop",
            certificate_title="Certificate of Completion",
            description="Successfully completed the workshop",
            issue_date="2026-10-11",
        )
        assert path.exists()
        assert path.stat().st_size > 0


def test_pdf_starts_with_pdf_header():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test_cert.pdf"
        generate_certificate_pdf(
            file_path=path,
            certificate_number="CERT-TEST002",
            recipient_name="Bob Smith",
            event_name="Python Workshop",
            certificate_title="Certificate of Completion",
            description="Successfully completed the workshop",
            issue_date="2026-10-11",
        )
        with open(path, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"


def test_pdf_long_name_does_not_crash():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "long_name.pdf"
        generate_certificate_pdf(
            file_path=path,
            certificate_number="CERT-LONG001",
            recipient_name="A" * 80,
            event_name="Workshop",
            certificate_title="Certificate",
            description="Desc",
            issue_date="2026-10-11",
        )
        assert path.exists()
