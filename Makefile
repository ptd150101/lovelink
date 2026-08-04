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
	docker compose exec backend python manage.py migrate

makemigrations:
	docker compose exec backend python manage.py makemigrations

superuser:
	docker compose exec backend python manage.py createsuperuser

test:
	docker compose exec backend pytest

lint:
	docker compose exec backend ruff check .
	docker compose exec frontend npm run lint
