# Crawlix — Distributed Web Scraping and Intelligence Platform

**Live:** [https://crawlix-chi.vercel.app](https://crawlix-chi.vercel.app)

A distributed web scraping and data intelligence platform built with FastAPI, Celery, Redis, PostgreSQL, and React.js. Users define crawl jobs that are broken into tasks and executed across multiple Celery workers in parallel. Once a job completes, an automated post-processing pipeline generates structured intelligence reports including pricing summaries, sentiment analysis, and entity extraction.

---

## Architecture

```
[ React.js Frontend (Vercel) ]
         |
   (REST / JWT + WebSocket)
         |
[ FastAPI API Gateway (AWS EC2) ] ───► [ PostgreSQL (Primary Storage) ]
         |
  (Task Dispatch + Telemetry)
         |
   [ Redis Broker ]
    |-- Queue: high_priority   (Job orchestration and heartbeats)
    |-- Queue: scraping_pool   (Distributed crawler workers)
    |-- Queue: ai_analysis     (Intelligence post-processing)
         |
[ Celery Worker Mesh (Worker 1, Celery Beat) ]
```

---

## Features

**Distributed Crawling**
- Multi-queue Celery task topology across `high_priority`, `scraping_pool`, and `ai_analysis` queues
- Real-time worker telemetry: CPU and RAM utilization, thread concurrency, and node heartbeats via WebSockets

**Scraping Engines**
- E-Commerce: price extraction, availability tracking, and discount detection
- News: article content extraction, sentiment polarity scoring, and named entity recognition
- Generic: JSON-LD / Schema.org parsing, OpenGraph metadata, and custom CSS selector support

**Intelligence Hub**
- Automated post-processing pipeline triggered on job completion
- Generates pricing intelligence, sentiment breakdowns, and entity summaries per job

**API and Security**
- FastAPI with JWT authentication (Argon2/Bcrypt), async database access, and WebSocket live log streaming
- SSRF protection, streaming download size limits, CSV formula injection sanitization, and strict CORS enforcement
- Unit and integration tests covering crawler engine behavior and task queue routing

**Data Export**
- One-click JSON and CSV export for downstream analytics or ML pipelines

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js, Vanilla CSS, Vite |
| Backend | Python, FastAPI, Celery, Celery Beat |
| Database | PostgreSQL, Redis |
| Infrastructure | AWS EC2, Docker Compose, Nginx, Let's Encrypt |
| Deployment | Vercel (frontend), DuckDNS + SSL (backend) |

---

## Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis and PostgreSQL (or use Docker Compose)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Celery Worker

```bash
cd backend
celery -A app.workers.celery_app worker -Q high_priority,scraping_pool,ai_analysis -l INFO
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Docker Deployment

Deploy the full production stack — PostgreSQL, Redis, FastAPI, Celery Workers, Celery Beat, and the React frontend — with a single command:

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
