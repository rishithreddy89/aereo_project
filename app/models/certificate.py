import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CertStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("certificate_jobs.id"), nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="PENDING", nullable=False
    )
    certificate_number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    job: Mapped["CertificateJob"] = relationship(  # noqa: F821
        "CertificateJob", back_populates="certificates"
    )

    __table_args__ = (
        Index("ix_certificates_job_id", "job_id"),
        Index("ix_certificates_status", "status"),
    )
