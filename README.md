# FlightsASL

FlightsASL is a FastAPI backend service scaffolded to run with Poetry-managed
dependencies.

## Prerequisites

1. Install Poetry (recommended via `pipx install poetry`).
2. Ensure `poetry` is on your `PATH` (restart the shell if needed).

## Setup

```bash
poetry install
```

This creates a virtual environment and installs FastAPI plus Uvicorn.

## Run the dev server

```bash
poetry run uvicorn src.main:app --reload --port 8000
```

Visit <http://127.0.0.1:8000/docs> for the interactive Swagger UI or
`http://127.0.0.1:8000/health` for a quick status check.