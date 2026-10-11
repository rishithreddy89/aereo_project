import pytest


def test_empty_recipients_rejected(client):
    payload = {
        "event_name": "Workshop",
        "certificate_title": "Certificate",
        "description": "Desc",
        "issue_date": "2026-10-11",
        "recipients": [],
    }
    resp = client.post("/api/v1/certificate-jobs", json=payload)
    assert resp.status_code == 422


def test_invalid_email_rejected(client):
    payload = {
        "event_name": "Workshop",
        "certificate_title": "Certificate",
        "description": "Desc",
        "issue_date": "2026-10-11",
        "recipients": [{"name": "Alice", "email": "not-an-email"}],
    }
    resp = client.post("/api/v1/certificate-jobs", json=payload)
    assert resp.status_code == 422


def test_invalid_date_rejected(client):
    payload = {
        "event_name": "Workshop",
        "certificate_title": "Certificate",
        "description": "Desc",
        "issue_date": "not-a-date",
        "recipients": [{"name": "Alice", "email": "alice@example.com"}],
    }
    resp = client.post("/api/v1/certificate-jobs", json=payload)
    assert resp.status_code == 422


def test_empty_name_rejected(client):
    payload = {
        "event_name": "Workshop",
        "certificate_title": "Certificate",
        "description": "Desc",
        "issue_date": "2026-10-11",
        "recipients": [{"name": "   ", "email": "alice@example.com"}],
    }
    resp = client.post("/api/v1/certificate-jobs", json=payload)
    assert resp.status_code == 422


def test_empty_event_name_rejected(client):
    payload = {
        "event_name": "",
        "certificate_title": "Certificate",
        "description": "Desc",
        "issue_date": "2026-10-11",
        "recipients": [{"name": "Alice", "email": "alice@example.com"}],
    }
    resp = client.post("/api/v1/certificate-jobs", json=payload)
    assert resp.status_code == 422


def test_missing_required_field(client):
    payload = {
        "certificate_title": "Certificate",
        "description": "Desc",
        "issue_date": "2026-10-11",
        "recipients": [{"name": "Alice", "email": "alice@example.com"}],
    }
    resp = client.post("/api/v1/certificate-jobs", json=payload)
    assert resp.status_code == 422
