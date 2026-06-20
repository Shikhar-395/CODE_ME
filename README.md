# CODE_ME

CODE_ME is a full-stack coding assessment platform inspired by LeetCode. Users can browse programming tests, solve questions in a browser-based code editor, and receive real-time submission results. Administrators can create tests, questions, and public or hidden test cases.

## Features

- User signup, login, and secure cookie-based sessions
- Role-based admin panel for managing tests and questions
- Monaco code editor with language-specific starter code
- Support for Python, C++, Java, and JavaScript
- Redis-backed submission queue and real-time WebSocket updates
- Docker-isolated code execution with CPU, memory, process, and timeout limits
- Public and hidden test cases
- Optional demo data seeding

## Tech stack

- **Frontend:** React, TypeScript, Vite, Monaco Editor
- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Database:** PostgreSQL or SQLite
- **Queue and events:** Redis
- **Code execution:** Docker
- **Authentication:** JWT session cookies with Argon2 password hashing

## Project structure

```text
.
├── backend/        FastAPI API, authentication, database, worker, and WebSockets
├── frontend/       React and TypeScript web application
├── docker/judge/   Sandboxed multi-language code runner
├── deploy/         Nginx, systemd, and EC2 deployment scripts
├── tests/          Backend and judge tests
└── docker-compose.yml
```

## Run locally with Docker

### Prerequisites

- Docker with Docker Compose

### 1. Configure the environment

Copy `.env.docker.example` to `.env` and update the credentials:

```bash
cp .env.docker.example .env
```

Generate a session secret with:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

### 2. Start the complete application

```bash
docker compose up --build
```

This starts:

- React/Vite frontend: `http://localhost:5173`
- FastAPI backend: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Submission worker and isolated judge containers
- PostgreSQL and Redis

Frontend edits under `frontend/` are picked up automatically by Vite without
rebuilding the image. Backend API edits also reload automatically. Rebuild only
when dependency files or Dockerfiles change.

```bash
docker compose down
```

Use `-v` only when you also want to delete local PostgreSQL and Redis data:

```bash
docker compose down -v
```

## Run services directly on the host

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

docker compose up -d postgres redis

uvicorn backend.main:app --reload
python -m backend.worker

cd frontend
npm install
npm run dev
```

## Tests

Run the backend unit tests:

```bash
python -m unittest discover -v
```

After building the judge image, run the Docker smoke test:

```bash
python -m backend.docker_smoke_test
```

## Deployment

The `deploy/` directory contains scripts and service definitions for deploying the API, worker, Redis, Nginx, and Docker judge on an Ubuntu EC2 instance. See [`deploy/README.md`](deploy/README.md) for details.
