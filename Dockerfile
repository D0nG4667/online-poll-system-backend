# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Install uv
# COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Compile bytecode
ENV UV_COMPILE_BYTECODE=1

# Working directory
WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Final image
FROM python:3.13-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder
COPY --from=builder /app/.venv /app/.venv

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Copy project files
COPY . .

# Collect static files
# RUN python manage.py collectstatic --noinput
# (Commented out: connect to DB usually needed, or use a build arg dummy secret key)

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
