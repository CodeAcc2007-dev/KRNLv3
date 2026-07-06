<div align="center">

# KRNL

### Your unified campus email & deadline portal.

An email-intelligence PWA for IIT Bombay students. Connect your webmail and KRNL turns a
firehose of institute mail into a sorted inbox, an automatic deadline tracker, and an
inbox you can ask questions in plain English.

**[🚀 Live app → krnlv3.vercel.app](https://krnlv3.vercel.app)**

![Status](https://img.shields.io/badge/status-live_in_production-3FB950)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-React_+_Vite-4C8DFF)
![PWA](https://img.shields.io/badge/PWA-installable-purple)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

</div>

---

## The problem

An IITB inbox is a firehose — placement notices, club recruitments, fest registrations,
talks, fee circulars, safety advisories — all in one flat, unsorted stream. The deadline
that actually matters to *you* is buried under fifty that don't, and by the time you scroll
to it, it's closed.

KRNL reads your mail so you don't have to.

## Features

| | |
|---|---|
| 📥 **Sorted inbox** | Every mail auto-categorized into Important, Academic, Opportunities & Announcements — no folders, no rules. |
| ⭐ **Personalized "Important"** | Ranked by what's consequential *and* the interests you pick, so the right things rise to the top. |
| 🗓️ **Automatic deadlines** | Dates and times are extracted from the email body and laid out as a sorted list + calendar. |
| 💬 **Ask KRNL** | Ask your inbox in plain English — *"what's due this week?"*, *"any internship openings?"* — answered from your own mail with citations. |
| 🔔 **Timely nudges** | A push 24h before a deadline, an alert when important mail lands, and a Sunday-evening weekly digest. |
| 📲 **Installable PWA** | Add to home screen; works like a native app, offline-aware. |
| 🔒 **Private by design** | Connects via an institute **access token, never your password**; credentials encrypted at rest; per-user data isolation. |

## Screenshots

*Drop `inbox.png`, `ask.png`, `deadlines.png` into `docs/assets/`, then uncomment the gallery below.*

<!-- Screenshot gallery — uncomment once the images are added to docs/assets/
| Inbox — Important | Ask KRNL | Deadlines |
|---|---|---|
| ![Inbox](docs/assets/inbox.png) | ![Ask](docs/assets/ask.png) | ![Deadlines](docs/assets/deadlines.png) |
-->


## Tech stack

**Frontend** — React + TypeScript, Vite, PWA (service worker, Web Push), Supabase JS (auth), deployed on **Vercel**.

**Backend** — FastAPI (Python 3.12), **Celery + Redis** for async sync and scheduled jobs, **Supabase / Postgres** for data, **Qdrant** for vector search, **Google Gemini** for extraction & embeddings, `pywebpush` for notifications. Containerized; deployed on **Railway** (Docker / Oracle VM alternative documented).

**Auth & mail** — Supabase Auth (Google OAuth) for the app; IMAP for institute mail, with tokens encrypted at rest (Fernet).

See **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for the full system design and sync pipeline, and **[docs/DECISIONS.md](docs/DECISIONS.md)** for the key trade-offs (rate limits, priority model, notifications).

## Getting started (local)

**Prerequisites:** Python 3.12, Node 18+, Redis (or `podman run -d --name redis --network=host redis:7-alpine`), and cloud accounts for Supabase, Qdrant, and Google Gemini.

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in Supabase / Qdrant / Gemini / VAPID values
python scripts/gen_vapid_keys.py   # generate a Web Push keypair for .env
```

Apply the SQL files in `backend/migrations/` in your Supabase SQL editor, then run the API
and worker in two terminals:

```bash
uvicorn app.main:app --reload
celery -A app.core.celery_app worker --concurrency=1 -B --loglevel=info
```

### 2. Frontend

```bash
cd frontend
npm install
# create .env.local with:
#   VITE_API_URL=http://localhost:8000
#   VITE_SUPABASE_URL=https://<your-project>.supabase.co
#   VITE_SUPABASE_ANON_KEY=<your-anon-key>
npm run dev
```

## Deployment

A full runbook (Railway primary, self-hosted Docker / Oracle Free VM alternative, Vercel
frontend) lives in **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**.

## Roadmap

- Per-user Gemini keys (BYOK) / billing tier to lift the shared free-tier ceiling
- Broader deadline & event extraction coverage
- Richer Ask KRNL retrieval and answers
- Notification preferences per category and per interest

## License

[MIT](LICENSE) — built by an IIT Bombay student. Contributions and issues welcome.
