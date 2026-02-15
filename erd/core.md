```mermaid
erDiagram
    %% Core Polling System ERD
    %% Domain: Polls, Questions, Options, Votes

    User {
        uuid id PK
        string email UK
        string first_name
        string last_name
        datetime created_at
        datetime updated_at
    }

    Poll {
        int id PK
        uuid created_by_id FK
        string title
        text description
        string slug UK "8-char random"
        datetime start_date
        datetime end_date
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    Question {
        int id PK
        int poll_id FK
        string text
        string question_type "single, multiple, text"
        int order
        string slug UK "8-char random"
    }

    Option {
        int id PK
        int question_id FK
        string text
        int order
        string slug UK "8-char random"
    }

    Vote {
        int id PK
        uuid user_id FK
        int question_id FK
        int option_id FK
        string slug UK "8-char random"
        datetime created_at
        string session_key "Optional for anon"
    }

    %% Relationships
    User ||--o{ Poll : "creates"
    Poll ||--|{ Question : "contains"
    Question ||--|{ Option : "has"
    
    User ||--o{ Vote : "casts"
    Question ||--o{ Vote : "receives"
    Option ||--o{ Vote : "selected_in"

    %% Constraints
    %% Vote: unique_together(user, question)
```

## Rationale
- **User**: Central identity using custom auth model.
- **Poll**: The root aggregate. Contains validation logic (dates, active status). Identified publicly by `slug`.
- **Question**: Ordered items within a poll. Supports multiple types (Single/Multiple choice).
- **Option**: Choices for questions.
- **Vote**: Records a user's choice. 
    - Links to `User` to prevent multiple votes (via unique constraint).
    - Links to `Question` and `Option` to capture the exact choice.
    - Includes `slug` for individual vote verification/receipts.
