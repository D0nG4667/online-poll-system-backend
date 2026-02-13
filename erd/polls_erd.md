erDiagram
    User ||--o{ Poll : creates
    User ||--o{ Vote : casts
    
    Poll ||--o{ Question : contains
    Poll {
        int id
        string title
        text description
        datetime start_date
        datetime end_date
        bool is_active
        datetime created_at
        datetime updated_at
        int created_by_id FK
    }

    Question ||--o{ Option : includes
    Question ||--o{ Vote : receives
    Question {
        int id
        string text
        string question_type
        int order
        int poll_id FK
    }

    Option ||--o{ Vote : selected_in
    Option {
        int id
        string text
        int order
        int question_id FK
    }

    Vote {
        int id
        datetime created_at
        int user_id FK
        int question_id FK
        int option_id FK
    }
