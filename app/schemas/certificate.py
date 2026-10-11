from pydantic import BaseModel


class CertificateOut(BaseModel):
    certificate_id: str
    recipient_name: str
    recipient_email: str
    status: str
    certificate_number: str | None
    download_url: str | None

    model_config = {"from_attributes": True}
