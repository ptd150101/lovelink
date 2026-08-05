# Local development

Docker builds and native Python development use [uv](https://docs.astral.sh/uv/) in project mode. The backend declares Python `>=3.13,<3.14` and all dependencies in `backend/pyproject.toml`; `backend/uv.lock` pins the resolved environment.

## Full stack in Docker Compose

No host Python or uv installation is required when the whole stack runs in Docker:

```bash
cp .env.example .env
docker compose up --build
```

The backend image copies the pinned uv binary and installs the locked project environment into `/opt/venv`. Docker BuildKit caches uv downloads between builds.

## Infrastructure in Docker, frontend and backend on the host

This is the recommended workflow while developing application code. Docker runs PostgreSQL, Redis, MinIO and LiveKit, while Django, Celery and Next.js run directly on the host for faster reloads and easier debugging.

Create the Compose environment and the host-backend environment:

```powershell
Copy-Item .env.example .env
Copy-Item .env.host.example .env.host
```

Start only the infrastructure services:

```powershell
docker compose up -d postgres redis minio minio-init livekit
```

The Compose file publishes these local endpoints:

- PostgreSQL: `127.0.0.1:5432`
- Redis: `127.0.0.1:6379`
- MinIO API: `http://localhost:9000`
- MinIO console: `http://localhost:9001`
- LiveKit signal: `ws://localhost:7880`

PostgreSQL and Redis are bound to `127.0.0.1`, so they are available to host processes without being exposed to the local network. If either default port is already occupied, change `POSTGRES_EXPOSE_PORT` or `REDIS_EXPOSE_PORT` in `.env` and set the corresponding `POSTGRES_PORT` or `REDIS_URL` value in `.env.host`.

Install uv once on Windows:

```powershell
winget install --id=astral-sh.uv -e
```

Then run Django directly. There is no separate `uv python install`, `uv venv` or dependency-install command: the first `uv run` selects a compatible Python 3.13 interpreter, downloads it when needed, creates `backend/.venv` and synchronizes the locked dependencies automatically.

```powershell
cd backend
uv run --env-file ../.env.host python manage.py migrate
uv run --env-file ../.env.host python manage.py seed_reference_data
uv run --env-file ../.env.host python manage.py runserver 0.0.0.0:8000
```

Run Celery in separate terminals when background jobs are needed:

```powershell
cd backend
uv run --env-file ../.env.host celery -A config worker -l INFO
```

```powershell
cd backend
uv run --env-file ../.env.host celery -A config beat -l INFO
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/app
NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880
```

Then start Next.js:

```powershell
cd frontend
npm ci
npm run dev
```

Stop the infrastructure services without deleting their data:

```powershell
docker compose stop postgres redis minio livekit
```

To stop and remove their containers while keeping named volumes:

```powershell
docker compose down
```

## Native backend commands

On macOS or Linux, install uv with the official standalone installer or an operating-system package manager. From `backend/`, commands run through the project environment automatically:

```bash
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest
uv run ruff check .
```

An explicit synchronization step is optional and useful in CI or before working offline:

```bash
uv sync --frozen
```

Manage dependencies through project commands rather than `uv pip install`:

```bash
uv add package-name
uv add --dev package-name
uv remove package-name
```

These commands update `pyproject.toml` and `uv.lock`. Commit both files whenever dependencies change.
