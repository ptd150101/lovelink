# Local development

Docker builds and native Python development use [uv](https://docs.astral.sh/uv/) for Python installation, virtual-environment management and dependency installation.

## Full stack in Docker Compose

No host Python or uv installation is required when the whole stack runs in Docker:

```bash
cp .env.example .env
docker compose up --build
```

The backend image copies the pinned uv binary, creates `/opt/venv`, installs `backend/requirements.txt` into that environment and adds its executables to `PATH`. Docker BuildKit caches uv downloads between builds.

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

Install the backend environment once:

```powershell
cd backend
uv python install 3.13
uv venv --python 3.13
uv pip install -r requirements.txt
```

Prepare and start Django:

```powershell
uv run --env-file ../.env.host --no-sync python manage.py migrate
uv run --env-file ../.env.host --no-sync python manage.py seed_reference_data
uv run --env-file ../.env.host --no-sync python manage.py runserver 0.0.0.0:8000
```

Run Celery in separate terminals when background jobs are needed:

```powershell
cd backend
uv run --env-file ../.env.host --no-sync celery -A config worker -l INFO
```

```powershell
cd backend
uv run --env-file ../.env.host --no-sync celery -A config beat -l INFO
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

## Native backend setup

Install uv on Windows with WinGet:

```powershell
winget install --id=astral-sh.uv -e
```

On macOS or Linux, install uv with the official standalone installer or an operating-system package manager.

From the repository root:

```bash
cd backend
uv python install 3.13
uv venv --python 3.13
uv pip install -r requirements.txt
```

The environment is created at `backend/.venv`. Activation is optional because commands can run through uv directly:

```bash
uv run --no-sync python manage.py migrate
uv run --no-sync python manage.py seed_reference_data
uv run --no-sync python manage.py runserver
```

Run background workers in separate terminals:

```bash
uv run --no-sync celery -A config worker -l INFO
uv run --no-sync celery -A config beat -l INFO
```

Run backend validation:

```bash
uv run --no-sync python manage.py check
uv run --no-sync python manage.py makemigrations --check --dry-run
uv run --no-sync pytest
uv run --no-sync ruff check .
```

After changing `requirements.txt`, install the updated dependency set into the existing environment again:

```bash
uv pip install -r requirements.txt
```

The project currently keeps `requirements.txt` as the canonical dependency declaration, while uv replaces `virtualenv` and `pip` for environment creation and package installation.
