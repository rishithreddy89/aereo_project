# Bulk Certificate Generator — Backend API

A FastAPI backend that accepts bulk recipient lists, generates personalized PDF certificates, tracks job progress in MySQL, and serves completed certificates for download.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI |
| Database | MySQL 8+ |
| ORM | SQLAlchemy 2.0 |
| DB Driver | PyMySQL |
| Validation | Pydantic v2 |
| Migrations | Alembic |
| PDF | ReportLab |
| Testing | pytest + HTTPX |
| Server | Uvicorn |
| Config | pydantic-settings |

---

## Architecture

```
POST /api/v1/certificate-jobs
        │
        ▼
  FastAPI API process          MySQL
  ─────────────────            ──────────────────────
  Validates input        ───►  certificate_jobs (PENDING)
  Creates job + certs          certificates     (PENDING)
  Returns 202 + job_id

  Worker process (separate terminal)
  ─────────────────────────────────
  Polls for PENDING jobs
  SELECT ... FOR UPDATE (prevents double-processing)
  Generates PDFs via ReportLab
  Updates status per certificate
  Sets final job status
```

### Folder Structure

```
app/
  main.py                  FastAPI app, router registration
  core/
    config.py              pydantic-settings, DATABASE_URL property
    logging.py             stdout logging setup
  db/
    session.py             SQLAlchemy engine, SessionLocal, get_db
    base.py                DeclarativeBase
  models/
    certificate_job.py     CertificateJob ORM model + JobStatus constants
    certificate.py         Certificate ORM model + CertStatus constants
  schemas/
    certificate_job.py     Pydantic request/response schemas
    certificate.py         CertificateOut schema
  api/routes/
    health.py              GET /health
    certificate_jobs.py    POST + GET job endpoints
    certificates.py        GET download endpoint
  services/
    job_service.py         create_job, get_job
    certificate_service.py get_certificates_for_job, get_certificate
    pdf_generator.py       ReportLab PDF rendering
  workers/
    certificate_worker.py  Polling worker, SELECT FOR UPDATE, savepoints
  utils/
    storage.py             File path helpers, path traversal prevention

tests/
  conftest.py              Test DB setup, fixtures, table truncation
  test_job_creation.py
  test_validation.py
  test_pdf_generation.py
  test_job_status.py
  test_failure_handling.py
  test_certificate_download.py

alembic/
  versions/001_initial.py  Initial schema migration
.env.example
requirements.txt
README.md
```

---

## Local Setup (macOS, no Docker)

### 1. Python virtual environment

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install "pydantic[email]"
```

### 2. MySQL via Homebrew

```bash
brew install mysql
brew services start mysql
```

### 3. Create databases and application user

Connect as root and run:

```bash
mysql -u root -p<your_root_password> --socket=/tmp/mysql.sock
```

```sql
CREATE DATABASE certificate_db CHARACTER SET utf8mb4;
CREATE DATABASE certificate_test_db CHARACTER SET utf8mb4;
CREATE USER 'cert_user'@'localhost' IDENTIFIED BY 'cert_password_123';
GRANT ALL PRIVILEGES ON certificate_db.* TO 'cert_user'@'localhost';
GRANT ALL PRIVILEGES ON certificate_test_db.* TO 'cert_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

`.env` contents:

```
DB_USER=cert_user
DB_PASSWORD=cert_password_123
DB_HOST=localhost
DB_PORT=3306
DB_NAME=certificate_db

STORAGE_DIR=./certificates
MAX_RECIPIENTS_PER_JOB=500
WORKER_POLL_INTERVAL=5
```

Never commit `.env` to version control.

### 5. Apply migrations

```bash
alembic upgrade head
```

### 6. Start the API server (Terminal 1)

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 7. Start the worker (Terminal 2)

```bash
source .venv/bin/activate
python -m app.workers.certificate_worker
```

### 8. Run tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

### 9. Swagger UI

Open http://localhost:8000/docs

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| DB_USER | cert_user | MySQL username |
| DB_PASSWORD | — | MySQL password |
| DB_HOST | localhost | MySQL host |
| DB_PORT | 3306 | MySQL port |
| DB_NAME | certificate_db | Main database name |
| STORAGE_DIR | ./certificates | PDF storage directory |
| MAX_RECIPIENTS_PER_JOB | 500 | Max recipients per job |
| WORKER_POLL_INTERVAL | 5 | Worker poll interval (seconds) |

For tests, set `TEST_DB_URL` to override the test database connection string.

---

## API Endpoints

### Health check

```
GET /health
```

Response:
```json
{"status": "ok", "database": "ok"}
```

---

### Create a certificate job

```
POST /api/v1/certificate-jobs
```

Request body:
```json
{
  "event_name": "Python Developer Workshop",
  "certificate_title": "Certificate of Completion",
  "description": "Successfully completed the workshop",
  "issue_date": "2026-10-11",
  "recipients": [
    {"name": "Alice Johnson", "email": "alice@example.com"},
    {"name": "Bob Smith",    "email": "bob@example.com"}
  ]
}
```

Response `202 Accepted`:
```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "PENDING",
  "message": "Job accepted. 2 certificate(s) queued for generation."
}
```

curl example:
```bash
curl -s -X POST http://localhost:8000/api/v1/certificate-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Python Workshop",
    "certificate_title": "Certificate of Completion",
    "description": "Successfully completed the workshop",
    "issue_date": "2026-10-11",
    "recipients": [
      {"name": "Alice Johnson", "email": "alice@example.com"},
      {"name": "Bob Smith", "email": "bob@example.com"}
    ]
  }'
```

---

### Check job status

```
GET /api/v1/certificate-jobs/{job_id}
```

Response:
```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "COMPLETED",
  "total_count": 2,
  "success_count": 2,
  "failure_count": 0,
  "pending_count": 0,
  "processing_count": 0,
  "created_at": "2026-10-11T10:00:00",
  "started_at": "2026-10-11T10:00:01",
  "completed_at": "2026-10-11T10:00:03",
  "certificates": [
    {
      "certificate_id": "abc123",
      "recipient_name": "Alice Johnson",
      "recipient_email": "alice@example.com",
      "status": "COMPLETED",
      "error_message": null
    }
  ]
}
```

curl example:
```bash
curl -s http://localhost:8000/api/v1/certificate-jobs/<job_id>
```

---

### List certificates for a job

```
GET /api/v1/certificate-jobs/{job_id}/certificates
```

Response:
```json
[
  {
    "certificate_id": "abc123",
    "recipient_name": "Alice Johnson",
    "recipient_email": "alice@example.com",
    "status": "COMPLETED",
    "certificate_number": "CERT-A1B2C3D4E5",
    "download_url": "/api/v1/certificates/abc123/download"
  }
]
```

---

### Download a certificate

```
GET /api/v1/certificates/{certificate_id}/download
```

Returns the PDF file with `Content-Type: application/pdf`.

curl example:
```bash
curl -o alice_cert.pdf \
  http://localhost:8000/api/v1/certificates/<certificate_id>/download
```

Only certificates with status `COMPLETED` can be downloaded. Returns `404` for unknown IDs, pending/failed certificates, or missing files.

---

## Job and Certificate Statuses

### Job statuses

| Status | Meaning |
|---|---|
| PENDING | Queued, not yet picked up by worker |
| PROCESSING | Worker is actively generating PDFs |
| COMPLETED | All certificates generated successfully |
| COMPLETED_WITH_ERRORS | Some succeeded, some failed |
| FAILED | All certificates failed |

### Certificate statuses

| Status | Meaning |
|---|---|
| PENDING | Waiting to be processed |
| PROCESSING | PDF generation in progress |
| COMPLETED | PDF generated and available |
| FAILED | PDF generation failed (see error_message) |

---

## Worker

The worker is a separate Python process that polls MySQL every `WORKER_POLL_INTERVAL` seconds.

Start:
```bash
python -m app.workers.certificate_worker
```

Stop: `Ctrl+C`

**How it works:**
1. On startup, resets any `PROCESSING` jobs to `PENDING` (crash recovery).
2. Polls for the oldest `PENDING` job using `SELECT ... FOR UPDATE SKIP LOCKED`.
3. Marks the job `PROCESSING` and commits immediately (short lock).
4. For each `PENDING` certificate, uses a **savepoint** so a single PDF failure does not roll back the entire job.
5. Sets the final job status based on success/failure counts.

---

## Error Handling

- Pydantic validates all input; returns `422` with field-level error details.
- `404` for unknown job IDs, certificate IDs, and missing PDF files.
- Path traversal is prevented in the download endpoint via `safe_resolve()`.
- Per-certificate exceptions are caught; the error message is stored and the job continues.
- Worker exceptions are logged and the worker sleeps before retrying.

---

## Design Decisions and Trade-offs

**Separate worker process** — Jobs survive API restarts. The worker polls MySQL rather than using an in-process task queue, keeping the infrastructure simple (no Redis/Celery).

**SELECT FOR UPDATE SKIP LOCKED** — Prevents two workers from claiming the same job. Safe for a single worker; multiple workers would need testing.

**Savepoints for per-certificate failures** — `db.begin_nested()` creates a MySQL SAVEPOINT so a failed PDF rolls back only that certificate's changes, not the entire job transaction.

**UUIDs as primary keys** — Avoids sequential ID enumeration in download URLs.

**No PDF in MySQL** — PDFs are stored on the local filesystem. The DB stores only the file path. The download endpoint resolves paths safely and never exposes filesystem paths in responses.

**UPDATE statements in worker** — The worker uses `sqlalchemy.update()` rather than ORM object mutation to avoid stale instance state after savepoint rollbacks.

---

## Known Limitations

- **Single worker only** — Multiple concurrent workers are not tested. `SKIP LOCKED` prevents double-processing of jobs, but certificate-level locking is not implemented.
- **No retry logic** — A failed certificate stays `FAILED`. Re-running the worker will not retry it.
- **Crash recovery is job-level only** — If the worker crashes mid-job, the job resets to `PENDING` on restart, but already-completed certificates are not re-generated (they remain `COMPLETED`).
- **Local filesystem storage** — PDFs are stored locally. In production, use S3 or similar object storage.
- **No authentication** — All endpoints are public. Add OAuth2/API key middleware for production.
- **Worker poll interval** — The worker sleeps between polls. For low latency, reduce `WORKER_POLL_INTERVAL`.

---

## Future Enhancements

- S3 storage for PDFs
- API key or JWT authentication
- Retry failed certificates
- Multiple certificate templates
- Email delivery of certificates
- Pagination on list endpoints
- Prometheus metrics endpoint

---

## Complete Workflow (curl)

```bash
# 1. Create a job
JOB_ID=$(curl -s -X POST http://localhost:8000/api/v1/certificate-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Python Workshop",
    "certificate_title": "Certificate of Completion",
    "description": "Successfully completed the workshop",
    "issue_date": "2026-10-11",
    "recipients": [
      {"name": "Alice Johnson", "email": "alice@example.com"},
      {"name": "Bob Smith", "email": "bob@example.com"}
    ]
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")

echo "Job ID: $JOB_ID"

# 2. Check status (run after starting the worker)
curl -s http://localhost:8000/api/v1/certificate-jobs/$JOB_ID | python3 -m json.tool

# 3. List certificates
curl -s http://localhost:8000/api/v1/certificate-jobs/$JOB_ID/certificates | python3 -m json.tool

# 4. Download a certificate (replace <cert_id> with an ID from step 3)
curl -o alice.pdf http://localhost:8000/api/v1/certificates/<cert_id>/download
```
