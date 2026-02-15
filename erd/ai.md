```mermaid
erDiagram
    %% AI & RAG Layer ERD
    %% Domain: AI Context, Insights, RAG Vectors

    User {
        uuid id PK
    }

    Poll {
        int id PK
        string slug "8-char"
        string title
        text description
        json questions "Embedded for ingest"
    }

    AnalysisRequest {
        int id PK
        uuid user_id FK
        int poll_id FK
        text query
        text response
        string provider_used "openai/gemini"
        datetime created_at
    }

    PGVector {
        uuid id PK
        int poll_id FK "Metadata"
        vector embedding "1536 dim"
        text content "Chunked Poll Data"
    }

    %% Relationships
    User ||--o{ AnalysisRequest : "requests"
    Poll ||--o{ AnalysisRequest : "analyzed_in"
    Poll ||--o{ PGVector : "embedded_as"

    %% Rationale
    %% AnalysisRequest: Tracks user interactions with the AI insight agent.
    %% PGVector: Represents the logical vector store (Langchain/PGVector) where poll data is ingested for RAG.
```

## Rationale
- **AnalysisRequest**: Stores the history of AI insights generated for a poll, linking the user, the poll, and the specific query/response pair. Useful for audit and history display.
- **PGVector**: A logical representation of the vector embeddings stored in the database. Each poll's text data (title, questions, voting stats) is chunked and embedded here to provide context for the LLM.
