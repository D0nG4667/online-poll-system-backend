```mermaid
erDiagram
    %% Analytics Layer ERD
    %% Domain: Views, Engagement, Trends

    Poll {
        int id PK
    }

    User {
        uuid id PK
    }

    PollView {
        int id PK
        int poll_id FK
        uuid user_id FK "Nullable"
        datetime created_at
    }

    Vote {
        int id PK
        int poll_id FK
        datetime created_at
        string session_key
    }

    DistributionAnalytics {
        int id PK
        int poll_id FK
        string event_type
        datetime timestamp
    }

    %% Logical Aggregates (Not physical tables, but API Types)
    AnalyticsStats {
        int total_votes
        int total_views
        float response_rate
    }
    
    Trend {
        datetime date
        int count
    }

    %% Relationships
    Poll ||--o{ PollView : "viewed"
    User ||--o{ PollView : "viewed"
    Poll ||--o{ Vote : "received"
    Poll ||--o{ DistributionAnalytics : "distributed_via"

    %% Rationale
    %% PollView: Captures every render of a poll. Linked to User if authenticated, otherwise anonymous.
    %% AnalyticsStats/Trend: Represents the aggregated data structure returned by the GraphQL API.
```

## Rationale
- **PollView**: The base unit for engagement tracking. High write volume.
- **Aggregates**: The system relies on real-time aggregation of `Vote`, `PollView`, and `DistributionAnalytics` to calculate `AnalyticsStats` and `Trends`.
