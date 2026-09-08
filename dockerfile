# Build the browser bundle separately so Node is absent from the runtime image.
FROM node:22-bookworm-slim AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Resolve Python dependencies from the locked API project.
FROM ghcr.io/astral-sh/uv:0.9.28-python3.13-bookworm-slim AS python-build

WORKDIR /build
COPY api/pyproject.toml api/uv.lock ./api/
RUN uv export --project api --locked --no-dev --no-emit-project -o requirements.txt \
    && uv pip install --system --prefix /install -r requirements.txt

# The final image contains only Python, app code, installed dependencies, and static assets.
FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY --from=python-build /install /usr/local
COPY api/ ./api/
COPY agent/ ./agent/
COPY --from=frontend-build /build/frontend/dist ./frontend/dist/

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/agent/data \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --app-dir /app/api --host 0.0.0.0 --port ${PORT}"]
