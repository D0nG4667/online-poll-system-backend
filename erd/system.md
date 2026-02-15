```mermaid
erDiagram
    %% System & Infrastructure ERD
    %% Domain: Users, Background Tasks, Infrastructure

    subgraph Application
        User {
            uuid id PK
            string email UK
            string password
            datetime date_joined
        }
        
        AuditLog {
            int id PK
            uuid user_id FK
            string action
            datetime timestamp
            jsonb details
        }
    end

    subgraph Infrastructure
        PostgreSQL {
            string content "Primary Data & Vectors"
        }
        
        Redis {
            string content "Cache & Celery Broker"
        }
        
        CeleryWorker {
            string content "Async Task Execution"
        }
    end

    subgraph Celery_Results
        TaskResult {
            int id PK
            string task_id UK
            string status
            string result
            datetime date_done
        }
    end

    %% Relationships
    User ||--o{ AuditLog : "performs"
    PostgreSQL ||--|| User : "stores"
    Redis ||--|| CeleryWorker : "queues"
    CeleryWorker ||--o{ TaskResult : "produces"

    %% Rationale
    %% AuditLog: (Future) centralized tracking of critical user actions.
    %% TaskResult: Stores outcomes of async jobs (emails, analytics processing) via django-celery-results.
```

## Rationale
- **User**: The core identity provider (Custom User Model).
- **TaskResult**: Managed by `django-celery-results` to persist the state of background jobs (e.g., report generation, bulk emails).
- **Infrastructure**: Highlights the reliance on PostgreSQL for persistent storage (including Vectors via PGVector) and Redis for high-speed caching and message brokering.
