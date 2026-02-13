# Contributing to Project Nexus

## 🌳 GitFlow Branching Strategy

Project Nexus follows a strict **GitFlow** workflow to ensure stability and parallel development.

### Main Branches
- **`main`**: Production-ready code. Do not commit directly. Deploys to Production.
- **`develop`**: Integration branch for the next release. Deploys to Staging.

### Supporting Branches

#### 1. Feature Branches (`feature/*`)
- **Purpose**: New features or non-critical enhancements.
- **Source**: `develop`
- **Target**: `develop` (via Pull Request)
- **Naming**: `feature/feature-name` (e.g., `feature/auth-system`, `feature/poll-creation`)

#### 2. Bugfix Branches (`bugfix/*`)
- **Purpose**: Fixes for bugs found in `develop`.
- **Source**: `develop`
- **Target**: `develop`
- **Naming**: `bugfix/issue-description`

#### 3. Release Branches (`release/*`)
- **Purpose**: Preparation for a new production release (version bumping, final testing).
- **Source**: `develop`
- **Target**: `main` AND `develop`
- **Naming**: `release/vX.Y.Z`

#### 4. Hotfix Branches (`hotfix/*`)
- **Purpose**: Critical fixes for bugs in Production.
- **Source**: `main`
- **Target**: `main` AND `develop`
- **Naming**: `hotfix/incident-description`

---

## 📝 Commit Messages

We use **Semantic Commits** to automate versioning and changelogs.

Format: `<type>(<scope>): <subject>`

### Types
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools and libraries

### Examples
- `feat(auth): implement login with JWT validation`
- `docs(readme): add setup instructions`
- `chore(deps): upgrade django to 5.2.10`

---

## 🚀 Workflow Example

1. **Start a new feature**:
    ```bash
    git checkout develop
    git pull origin develop
    git checkout -b feature/my-cool-feature
    ```

2. **Commit changes**:
    ```bash
    git add .
    git commit -m "feat(poll): add websocket connection logic"
    ```

3. **Push & PR**:
    ```bash
    git push origin feature/my-cool-feature
    # Open Pull Request on GitHub targeting 'develop'
    ```

---

## 🛠 CI/CD & Code Quality

We maintain high code quality through automated checks.

### 1. Linting & Formatting
We use `ruff` for both linting and formatting. 
Before committing, ensure your code passes:
```bash
uv run ruff check . --fix
uv run ruff format .
```

### 2. Testing
Every PR must pass existing tests and include new tests for new features:
```bash
uv run pytest
```

### 3. CI Pipeline
Our GitHub Actions pipeline runs on every push to `develop` and `main`, and on every Pull Request. It checks:
- Python 3.13 compatibility
- Ruff linting and formatting
- Pytest execution with coverage reporting
- Automated database migrations (on Render)

### 4. Pull Request Template
Ensure you fill out the provided Pull Request template when opening a PR. This helps reviewers understand your changes quickly.
