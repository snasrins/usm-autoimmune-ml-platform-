# USM Autoimmune ML Platform

A full-stack machine learning platform for autoimmune disease research at Universiti Sains Malaysia (USM). Supports end-to-end model development — from data ingestion and training to registry management, comparison, and deployment — with a clean web interface and a robust REST API.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Environment Variables](#environment-variables)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Security Notes](#security-notes)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- Train and evaluate ML models (scikit-learn, XGBoost, LightGBM, CatBoost) on autoimmune disease datasets
- Model registry with MinIO-backed artifact storage and PostgreSQL metadata tracking
- Interactive model comparison with bar, radar, and line charts (Recharts)
- Secure JWT + OAuth2 authentication with researcher/admin role separation
- Background training jobs with FastAPI BackgroundTasks (Celery-ready for scale)
- Auto-generated Swagger/OpenAPI documentation
- Fully containerised via Docker and Docker Compose
- Cross-platform: Windows, Linux, macOS

---

## Tech Stack

### Backend

| Layer | Technology |
|---|---|
| Language | Python 3.9+ |
| Framework | FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Object Storage | MinIO (S3-compatible) |
| Authentication | JWT, OAuth2 (FastAPI) |
| Background Tasks | FastAPI BackgroundTasks / Celery (optional) |
| ML Libraries | scikit-learn, XGBoost, LightGBM, CatBoost, pandas, numpy |
| Serialization | Pydantic |
| API Docs | Swagger UI / OpenAPI (auto-generated) |
| Logging | Python `logging` module |
| Configuration | `.env`, `config.py` |

### Frontend

| Layer | Technology |
|---|---|
| Language | JavaScript (ES6+) |
| Framework | React 18 |
| Build Tool | Vite |
| Charting | Recharts 3.8.1 |
| HTTP Client | Axios |
| Icons | Lucide React |
| State Management | React Hooks (useState, useEffect, useContext) |
| Routing | React Router |
| Styling | CSS Modules / plain CSS |

### DevOps & Infrastructure

| Layer | Technology |
|---|---|
| Containerisation | Docker, Docker Compose |
| Version Control | Git |
| Scripting | Bash (`.sh`), PowerShell (`.ps1`) |
| CI/CD | GitHub Actions *(configurable)* |
| Reverse Proxy | Nginx *(optional)* |
| Monitoring | Prometheus / Grafana *(optional)* |

---

## Architecture

```
+-----------------------+          +----------------------------+
|  React 18 Frontend    |<--REST-->|  FastAPI Backend (:8001)   |
|  (Vite, Recharts)     |          |  SQLAlchemy ORM            |
+-----------------------+          +------------+---------------+
                                                |
                        +-----------------------+------------------+
                        v                       v                  v
                  +----------+           +----------+    +--------------+
                  |PostgreSQL|           |  MinIO   |    |  ML Engine   |
                  |(metadata,|           |(models,  |    |(sklearn, XGB,|
                  |jobs,users|           |datasets) |    | LightGBM...) |
                  +----------+           +----------+    +--------------+
```

---

## Project Structure

```
usm-autoimmune-ml-platform/
├── app/                        # FastAPI backend
│   ├── api/                    # Route handlers (v1)
│   ├── core/                   # Config, security, logging
│   ├── db/                     # Database session, base models
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── services/               # Business logic (ML, MinIO, jobs)
│   └── main.py                 # App entrypoint
├── frontend/                   # React 18 frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Route-level pages
│   │   ├── hooks/              # Custom React hooks
│   │   ├── api/                # Axios API clients
│   │   └── main.jsx            # React entrypoint
│   ├── .env                    # Frontend environment config
│   ├── index.html
│   └── vite.config.js
├── docker-compose.yml          # Multi-service orchestration
├── Dockerfile                  # Backend container build
├── requirements.txt            # Python dependencies
├── .env                        # Backend env variables (do not commit)
├── .env.example                # Example environment template
├── test_*.py                   # Backend test files
├── *.sh                        # Bash utility scripts
├── *.ps1                       # PowerShell utility scripts
└── README.md
```

---

## Requirements

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- Git
- *(Optional)* NVIDIA GPU + CUDA drivers for accelerated training

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values. **Never commit `.env` to a public repository.**

```env
# === MinIO Object Storage ===
MINIO_ROOT_USER=minio_admin
MINIO_ROOT_PASSWORD=your_minio_password
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minio_admin
MINIO_SECRET_KEY=your_minio_password
MINIO_SECURE=false
MINIO_BUCKET=ml-models

# === PostgreSQL ===
DATABASE_URL=postgresql://usm_db_admin:your_db_password@localhost:5432/usm_autoimmune_registry

# === FastAPI ===
API_V1_STR=/api/v1
JWT_SECRET_KEY=your_jwt_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=60

# === App ===
ENVIRONMENT=development
DEBUG=true
```

For the frontend, create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8001/api/v1
```

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/usm-autoimmune-ml-platform.git
cd usm-autoimmune-ml-platform
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Start Infrastructure (MinIO + PostgreSQL)

```bash
docker-compose up -d minio postgres
```

- **MinIO Console:** http://localhost:9001
- **PostgreSQL:** localhost:5432

Once MinIO is running, log in to the console and create a bucket named `ml-models`.

### 4. Start the Backend

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

- API: http://localhost:8001
- Swagger docs: http://localhost:8001/docs

### 5. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

App will be available at http://localhost:3000 (or the next available port).

### 6. (Alternative) Full Stack with Docker Compose

```bash
docker-compose up --build
```

This starts MinIO, PostgreSQL, the FastAPI backend, and the React frontend together.

---

## Usage

| Feature | How to Access |
|---|---|
| **Model Registry** | Navigate to the Registry page to view all synced models |
| **Sync from MinIO** | Click "Sync from MinIO" to import model artifacts from object storage |
| **Model Comparison** | Select models in the registry and open the Comparison view |
| **Launch Training Job** | Use the Training page or POST `/api/v1/jobs` via Swagger |
| **User Management** | Admin panel or `/api/v1/users` endpoints |
| **Data Export** | Use the export button or utility scripts in the repo root |

---

## API Documentation

FastAPI generates interactive API docs automatically:

- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

Key endpoint groups:

| Prefix | Description |
|---|---|
| `/api/v1/auth` | Login, token refresh |
| `/api/v1/users` | User management |
| `/api/v1/jobs` | Training job lifecycle |
| `/api/v1/models` | Model registry CRUD |
| `/api/v1/storage` | MinIO sync and artifact access |

---

## Testing

### Backend

```bash
pytest test_*.py -v
```

### Frontend

```bash
cd frontend
npm run test
```

### Linting

```bash
# Python
flake8 app/
black app/ --check

# JavaScript
cd frontend
npx eslint src/
npx prettier src/ --check
```

---

## Security Notes

- JWT secrets and database passwords must be strong, randomly generated values in production.
- `.env` files must **never** be committed to version control — add them to `.gitignore`.
- Role-based access control (Researcher / Admin) is enforced at the API level.
- For production, enable HTTPS via an Nginx reverse proxy and set `MINIO_SECURE=true`.

---

## Deployment

### Local / On-Premise

Use `docker-compose up --build` for a single-command deployment on any machine with Docker installed.

### Cloud VM

1. Provision a VM (e.g., AWS EC2, Azure VM, or any Linux server).
2. Install Docker and Docker Compose.
3. Clone the repo, configure `.env`, and run `docker-compose up -d`.
4. *(Optional)* Place Nginx in front for HTTPS termination.

### GPU Support

Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) and add the following to the backend service in `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

---

## Troubleshooting

**500 Error on MinIO Sync**
Ensure `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, and `MINIO_ENDPOINT` are correctly set in `.env`. Restart the backend after any `.env` changes.

**No Models Appear in Registry**
Click "Sync from MinIO" after confirming model files exist in the `ml-models` bucket via the MinIO console.

**Database Connection Refused**
Verify `DATABASE_URL` in `.env` and confirm PostgreSQL is running with `docker-compose ps`.

**Frontend Cannot Reach API**
Check that `VITE_API_BASE_URL` in `frontend/.env` points to the correct backend host and port, and that CORS is enabled in `app/main.py`.

**Port Already in Use**
Change the port mapping in `docker-compose.yml` or pass `--port` to `uvicorn` / `npm run dev`.

---

## Contributing

1. Fork the repository and create a feature branch: `git checkout -b feature/your-feature`
2. Follow the existing code style (black + flake8 for Python, ESLint + Prettier for JS).
3. Write or update tests for any changed functionality.
4. Open a pull request with a clear description of your change.

---

*For questions or support, please open an issue on GitHub or contact the platform maintainer.*