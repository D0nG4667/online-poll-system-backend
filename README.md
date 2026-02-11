# Online Poll System Backend 🚀

A robust, AI-powered backend for creating, managing, and analyzing polls. Built with Django 5, Celery, and LangChain, featuring high-performance voting, RAG-based insights, and dual authentication support (Session + JWT).

## ✨ Key Features

- **AI-Powered Poll Generation**: Build entire polls from natural language prompts using LLMs.
- **RAG Insights**: Advanced analysis of poll results using Retrieval-Augmented Generation (PGVector).
- **Dual Authentication**: Support for both traditional session-based (Django) and modern JWT-based (Headless) access.
- **High-Performance Voting**: Real-time vote aggregation with concurrency controls and background processing.
- **Advanced Querying**: GraphQL schema (Strawberry) for complex data retrieval.
- **Automation**: Asynchronous tasks for notifications and heavy computations via Celery.

## 🛠 Tech Stack

- **Core**: Python 3.13, Django 5.2, Django REST Framework.
- **AI/RAG**: LangChain, OpenAI, Google Gemini, PGVector.
- **Database**: PostgreSQL (Neon), Redis (Upstash).
- **GraphQL**: Strawberry Django.
- **Background Tasks**: Celery, Redis.
- **Monitoring**: Sentry SDK.

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- API Keys (OpenAI or Gemini) configured in `.env`

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd online-poll-system-backend
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Fill in your DATABASE_URL, REDIS_URL, OPENAI_API_KEY, etc.
   ```

3. **Build and start services**:
   ```bash
   docker-compose up --build
   ```

4. **Initialize Database**:
   ```bash
   docker-compose exec web uv run python manage.py migrate
   docker-compose exec web uv run python manage.py createsuperuser
   ```

## 📖 API Documentation

- **Swagger UI**: [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/)
- **Auth UI**: [http://localhost:8000/api/schema/auth-ui/](http://localhost:8000/api/schema/auth-ui/)
- **GraphQL Playground**: [http://localhost:8000/graphql/](http://localhost:8000/graphql/)

## 🧪 Testing

The project maintains an **82% test coverage** suite.

```bash
# Run all tests
docker-compose exec web uv run pytest

# Run with coverage report
docker-compose exec web uv run pytest --cov=apps --cov-report=term-missing
```

## 📜 Infrastructure & Ops

- **CI/CD**: GitHub Actions for automated linting, formatting (Ruff/Prettier), and testing.
- **Deployment**: Configured for Render via `render.yaml`.
- **Telemetry**: Sentry integration for real-time error tracking.

---
Built with ❤️ by Gabriel Okundaye (ProDev FullStack Engineer)
