# Local development

Docker builds and native Python development use [uv](https://docs.astral.sh/uv/) for Python installation, virtual-environment management and dependency installation.

## Docker Compose

No host Python or uv installation is required when the whole stack runs in Docker:

```bash
cp .env.example .env
docker compose up --build
```

The backend image copies the pinned uv binary, creates `/opt/venv`, synchronizes `backend/requirements.txt` into that environment and adds its executables to `PATH`. Docker BuildKit caches uv downloads between builds.

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
uv pip sync requirements.txt
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

After changing `requirements.txt`, synchronize the existing environment again:

```bash
uv pip sync requirements.txt
```

`uv pip sync` removes packages that are not declared in the requirements file, keeping local and CI environments aligned.
