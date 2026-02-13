# ---- Stage 1: Builder ----
FROM python:3.13-slim-bookworm AS builder

# Copy uv binary from Astral's official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create app directory
RUN mkdir /app
WORKDIR /app

# Environment optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies (compilers, headers, pkg-config, Postgres client dev libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc pkg-config libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for caching)
COPY pyproject.toml uv.lock /app/

# Install dependencies only (no project code yet)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Copy project code
COPY . /app

# Sync the project (installs the project itself if configured as package, or just finalizes venv)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Precompile bytecode
ENV UV_COMPILE_BYTECODE=1

# ---- Stage 2: Runtime ----
FROM python:3.13-slim-bookworm

# Create non-root user and app dir
RUN useradd -m -r appuser && \
    mkdir /app && \
    chown -R appuser /app

WORKDIR /app

# Copy app code + .venv together from builder
COPY --from=builder --chown=appuser:appuser /app /app

# Install only runtime libraries (no compilers) - Postgres client
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Ensure .venv/bin is first on PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8000

# Copy uv binary from Astral's official image (useful for runtime management commands if needed)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Collect static files
RUN export DJANGO_SECRET_KEY=dummy && \
    export DATABASE_URL=sqlite:////tmp/db.sqlite3 && \
    export REDIS_URL=redis://localhost:6379/0 && \
    export BREVO_API_KEY=dummy && \
    export JWT_PRIVATE_KEY="dummy_key" && uv run python manage.py collectstatic --noinput # pragma: allowlist secret

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health/ || exit 1

# Start the application using Gunicorn
CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
