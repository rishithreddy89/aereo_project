VALID_PAYLOAD = {
    "event_name": "Python Workshop",
    "certificate_title": "Certificate of Completion",
    "description": "Successfully completed the workshop",
    "issue_date": "2026-10-11",
    "recipients": [
        {"name": "Alice Johnson", "email": "alice@example.com"},
        {"name": "Bob Smith", "email": "bob@example.com"},
    ],
}


def test_create_job_returns_202(client):
    resp = client.post("/api/v1/certificate-jobs", json=VALID_PAYLOAD)
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"


def test_create_job_returns_job_id(client):
    resp = client.post("/api/v1/certificate-jobs", json=VALID_PAYLOAD)
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    assert len(job_id) == 36  # UUID format


def test_create_job_message_contains_count(client):
    resp = client.post("/api/v1/certificate-jobs", json=VALID_PAYLOAD)
    assert "2" in resp.json()["message"]
