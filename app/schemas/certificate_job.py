from datetime import date
from pydantic import BaseModel, EmailStr, field_validator
from app.core.config import settings


class RecipientIn(BaseModel):
    name: str
    email: EmailStr

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Recipient name cannot be empty")
        if len(v) > 255:
            raise ValueError("Recipient name too long")
        return v


class CertificateJobCreate(BaseModel):
    event_name: str
    certificate_title: str
    description: str
    issue_date: date
    recipients: list[RecipientIn]

    @field_validator("recipients")
    @classmethod
    def recipients_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Recipient list cannot be empty")
        if len(v) > settings.MAX_RECIPIENTS_PER_JOB:
            raise ValueError(f"Exceeds maximum of {settings.MAX_RECIPIENTS_PER_JOB} recipients per job")
        return v

    @field_validator("event_name", "certificate_title", "description")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v


class CertificateJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class CertificateJobStatus(BaseModel):
    job_id: str
    status: str
    total_count: int
    success_count: int
    failure_count: int
    pending_count: int
    processing_count: int
    created_at: str
    started_at: str | None
    completed_at: str | None
    certificates: list[dict]

    model_config = {"from_attributes": True}
