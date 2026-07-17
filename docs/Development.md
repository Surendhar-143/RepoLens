# Local Development Guide

Follow this guide to set up, format, test, and run the RepoLens platform locally.

## Prerequisite Tooling
* Python 3.13
* Node.js 20 or higher
* Docker & Docker Compose

---

## Local Setup

### 1. Backend Application
Navigate to `apps/api` to configure the Python environment:
```bash
cd apps/api
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

Run migrations locally:
```bash
alembic upgrade head
```

Run FastAPI developer server:
```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Worker Application
Navigate to `apps/worker` to configure the background worker:
```bash
cd apps/worker
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

Run worker:
```bash
arq app.main.WorkerSettings
```

### 3. Web Frontend
Navigate to `apps/web` to configure the React workspace:
```bash
cd apps/web
npm install
npm run dev
```
The client dashboard runs at [http://localhost:3000](http://localhost:3000).

---

## Code Quality Checklists

### Linting & Formatting
We check python files using Ruff and format using Black.
```bash
black --check apps/api apps/worker
ruff check apps/api apps/worker
```

Verify frontend compilation and ESLint:
```bash
cd apps/web
npm run lint
```

### Testing Suites
Run backend unit and route tests:
```bash
cd apps/api
pytest
```
