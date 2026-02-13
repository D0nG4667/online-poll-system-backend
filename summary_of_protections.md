# CI/CD Pipeline Protections & Enforcements

This document summarizes the quality, security, and robustness standards now enforced in the project pipeline.

## 1. Local Development (Pre-Commit)
Commits are **blocked** unless the following checks pass:

| Check Type | Tool | Enforcement |
| :--- | :--- | :--- |
| **Linting** | `ruff` | No unused imports, variables, dead code, or complexity violations (>10). strict subset of rules enabled. |
| **Formatting** | `ruff format` | Code must be Black-compatible. |
| **Import Sorting** | `ruff` | Imports must be sorted (isort-compatible) and organized by section. |
| **Type Checking** | `mypy` | Strict type checking with Django and DRF stubs. No untyped definitions allowed. |
| **Secrets** | `detect-secrets` | No hardcoded secrets allowed (compared against `.secrets.baseline`). |
| **Vulnerabilities** | `safety` | No known vulnerabilities in installed dependencies. |
| **Django Config** | Custom Script | `DEBUG = True` is forbidden in production settings. |
| **Migrations** | Custom Script | All model changes must have corresponding migrations. |

## 2. GitHub Actions CI/CD
Pull Requests and Merges to main/develop branches trigger the following:

| Stage | Check | Failure Condition |
| :--- | :--- | :--- |
| **Quality** | `pre-commit` | Fails if any local hook fails (redundancy check). |
| **Security** | `trivy` (Config) | Fails on critical/high misconfigurations in Dockerfile or IaC. |
| **Security** | `safety` | Fails on vulnerable dependencies. |
| **Testing** | `pytest` | Fails if any test fails. Run inside Docker with Postgres service. |
| **Coverage** | `pytest-cov` | Fails if coverage is under **80%**. Reports uploaded to Codecov. |
| **Docker** | `docker build` | Fails if Docker image cannot be built (multi-stage, non-root). |
| **Container** | `trivy` (Image) | Fails if built image contains critical/high OS or library vulnerabilities. |

## 3. Docker Security
- **Non-Root User**: Application runs as `appuser`, not root.
- **Multi-Stage Build**: Build dependencies (gcc, etc.) are stripped from runtime image.
- **Healthcheck**: Container reports healthy only if application responds to `/health/`.
- **No Secrets**: Secrets are injected via environment variables, not baked into the image.

## 4. Blocking Conditions
Deployments (if configured) or Merges are blocked if:
- [ ] Tests fail or coverage < 80%.
- [ ] Any linter or formatter error exists.
- [ ] Type checks fail.
- [ ] Vulnerabilities are detected in code or container.
- [ ] Migrations are missing.
- [ ] `DEBUG=True` in production.
