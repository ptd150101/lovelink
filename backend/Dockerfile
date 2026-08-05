# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:0.12.1 AS uv
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV VIRTUAL_ENV=/opt/venv
ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates libpq5 libjpeg62-turbo zlib1g && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /bin/
RUN uv venv /opt/venv

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/uv uv pip sync --python /opt/venv/bin/python requirements.txt

COPY . .
EXPOSE 8000
