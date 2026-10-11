import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class JobStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"


class CertificateJob(Base):
    __tablename__ = "certificate_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    certificate_title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    issue_date: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum("PENDING", "PROCESSING", "COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED"),
        default="PENDING",
        nullable=False,
    )
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    certificates: Mapped[list["Certificate"]] = relationship(  # noqa: F821
        "Certificate", back_populates="job", lazy="select"
    )
