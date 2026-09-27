# 🌐 Crawlix: Distributed Web Scraping & Intelligence Platform

> A production-grade, distributed web scraping and intelligence platform engineered with **FastAPI**, **Celery**, **Redis**, **PostgreSQL**, and **React.js**.

---

## ⚡ Highlights & Key Technical Features (For Resume Showcase)

- **Distributed Worker Mesh**: Multi-node Celery task execution topology consuming from priority queues (`high_priority`, `scraping_pool`, `ai_analysis`).
- **Dynamic Telemetry & Heartbeat Registry**: Real-time worker health, CPU/RAM utilization, thread concurrency, and node metrics.
- **Intelligent Scraping Engines**:
  - **E-Commerce & Pricing Intelligence**: Price history, discount calculations, out-of-stock tracking.
  - **News & Sentiment Engine**: Article content extraction, sentiment score calculation, key named entity recognition.
  - **Generic Structured Ingestion**: JSON-LD / Schema.org parser, OpenGraph metadata, and custom CSS selector extraction.
- **Async API Gateway**: Built with FastAPI, JWT Authentication (Argon2/Bcrypt + secure claims), and WebSockets for live crawl log streaming.
- **Dark Glassmorphic UI**: Built with React.js and pure Vanilla CSS (modularized per component/page in `src/styles`).
- **Data Export**: 1-Click structured JSON and CSV exporter for downstream ML/analytics pipelines.

---

## 🏗️ Architecture Overview

```
[ React.js Frontend ] 
        │
   (REST / JWT & WebSocket)
        ▼
[ FastAPI API Gateway ] ───► [ PostgreSQL (Primary Storage) ]
        │
   (Task Dispatch & Telemetry)
        ▼
  [ Redis Broker ] 
   ├── Queue: high_priority (Job orchestration & heartbeats)
   ├── Queue: scraping_pool (Distributed web crawler nodes)
   └── Queue: ai_analysis   (NLP sentiment & price aggregators)
        ▲
        │ (Task Ingestion & State Reporting)
[ Celery Worker Mesh (Worker 1, Worker 2, Celery Beat) ]
```

---

## 🚀 Quickstart Guide (Local Development)

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- Redis & PostgreSQL (or use Docker Compose)

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Celery Worker (In a separate terminal)
```bash
cd backend
celery -A app.workers.celery_app worker -Q high_priority,scraping_pool,ai_analysis -l INFO
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🐳 One-Command Deployment with Docker Compose

To deploy the entire production stack (PostgreSQL, Redis, FastAPI, 2 Celery Workers, Celery Beat, and React Frontend):

```bash
docker compose up --build
```
- Frontend UI: `http://localhost:3000`
- API Swagger Docs: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`
