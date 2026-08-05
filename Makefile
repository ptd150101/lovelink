.PHONY: up down build logs migrate makemigrations superuser test lint
up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

migrate:
	docker compose exec backend uv run --frozen python manage.py migrate

makemigrations:
	docker compose exec backend uv run --frozen python manage.py makemigrations

superuser:
	docker compose exec backend uv run --frozen python manage.py createsuperuser

test:
	docker compose exec backend uv run --frozen pytest

lint:
	docker compose exec backend uv run --frozen ruff check .
	docker compose exec frontend npm run lint
