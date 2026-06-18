# CODE_ME

CODE_EXEC is a full-stack coding assessment platform inspired by LeetCode. Users can browse programming tests, solve questions in a browser-based code editor, and receive real-time submission results. Administrators can create tests, questions, and public or hidden test cases.

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

## Run locally

### Prerequisites

- Python 3.10+
- Node.js and npm
- Docker with Docker Compose

### 1. Install backend dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start PostgreSQL and Redis

```bash
docker compose up -d postgres redis
```

### 3. Configure the environment

Create a `.env` file in the project root:

```dotenv
DATABASE_URL=postgresql+asyncpg://leetcode:leetcode@127.0.0.1:55432/leetcode
REDIS_URL=redis://127.0.0.1:6379/0

SESSION_SECRET_KEY=replace-with-a-long-random-secret
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
CORS_ORIGINS=http://localhost:5173

JUDGE_EXECUTOR=docker
JUDGE_DOCKER_IMAGE=leetcode-judge:latest

AUTO_SEED_DEMO_DATA=true
SEED_ADMIN_NAME=Admin
SEED_ADMIN_USERNAME=admin@example.com
SEED_ADMIN_PASSWORD=change-this-password
```

Generate a session secret with:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

### 4. Build the judge image

```bash
chmod +x docker/build-judge.sh
./docker/build-judge.sh
```

### 5. Start the API and worker

Run these commands in separate terminals with the virtual environment active:

```bash
uvicorn backend.main:app --reload
```

```bash
python -m backend.worker
```

The API is available at `http://localhost:8000`, with interactive documentation at `http://localhost:8000/docs`.

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. If demo seeding is enabled, sign in with the admin credentials configured in `.env`.

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

