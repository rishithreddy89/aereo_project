VALID_PAYLOAD = {
    "event_name": "Python Workshop",
    "certificate_title": "Certificate of Completion",
    "description": "Successfully completed the workshop",
    "issue_date": "2026-10-11",
    "recipients": [
        {"name": "Alice Johnson", "email": "alice@example.com"},
    ],
}


def test_job_status_returns_correct_fields(client):
    job_id = client.post("/api/v1/certificate-jobs", json=VALID_PAYLOAD).json()["job_id"]
    resp = client.get(f"/api/v1/certificate-jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == job_id
    assert data["total_count"] == 1
    assert "status" in data
    assert "success_count" in data
    assert "failure_count" in data
    assert "pending_count" in data
    assert "processing_count" in data
    assert "certificates" in data


def test_job_status_404_for_unknown(client):
    resp = client.get("/api/v1/certificate-jobs/nonexistent-id")
    assert resp.status_code == 404


def test_list_certificates_returns_items(client):
    job_id = client.post("/api/v1/certificate-jobs", json=VALID_PAYLOAD).json()["job_id"]
    resp = client.get(f"/api/v1/certificate-jobs/{job_id}/certificates")
    assert resp.status_code == 200
    certs = resp.json()
    assert len(certs) == 1
    assert certs[0]["recipient_name"] == "Alice Johnson"
    assert certs[0]["status"] == "PENDING"


def test_list_certificates_404_for_unknown_job(client):
    resp = client.get("/api/v1/certificate-jobs/bad-id/certificates")
    assert resp.status_code == 404
