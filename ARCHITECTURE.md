# System Architecture 🏗️

The Online Poll System is designed for scalability and high availability, leveraging a service-oriented architecture with asynchronous processing and dedicated AI integration.

## 🌉 System Overview (C4 Level 2)

```mermaid
graph TB
    subgraph "Client Layer"
        User[Standard User]
        APIClient[Mobile/Web Client]
    end

    subgraph "Application Layer (Django)"
        Web[Web Server - Gunicorn/Uvicorn]
        API[DRF / Strawberry GraphQL]
        Worker[Celery Workers]
        Auth[allauth-headless / JWT]
    end

    subgraph "Storage & Messaging"
        PG[(PostgreSQL - Neon)]
        Vector[(PGVector - Search)]
        Redis[(Redis - Upstash)]
    end

    subgraph "External Services"
        LLM[OpenAI / Gemini API]
        Sentry[Error Tracking]
        Email[Brevo/Anymail]
    end

    User --> APIClient
    APIClient --> Web
    Web --> API
    API --> PG
    API --> Vector
    API --> Auth
    Worker --> PG
    Worker --> Redis
    Web --> Redis
    API --> LLM
    Worker --> Email
    Web --> Sentry
```

## 🧠 AI & RAG Data Flow

The system uses a Retrieval-Augmented Generation (RAG) pattern to ensure poll insights are grounded in actual user data while maintaining low latency.

```mermaid
sequenceDiagram
    participant U as User
    participant A as AI API
    participant S as RAGService
    participant V as Vector Store (PGVector)
    participant L as LLM (OpenAI/Gemini)

    Note over U, L: Poll Insight Generation
    U->>A: POST /api/v1/ai/generate-insight/ (query, poll_id)
    A->>S: invoke_rag_chain(poll_data)
    S->>V: similarity_search(query_vectors)
    V-->>S: relevant_snippets
    S->>L: generate_insight(snippets + poll_data)
    L-->>S: structured_insight
    S-->>A: response
    A-->>U: JSON Insight Result
```

## 🔐 Dual Authentication Strategy

We implement a multi-backend approach to support both traditional web sessions and stateless mobile/standalone clients.

- **DRF Default**: Uses `SessionAuthentication` and `HeadlessJWTAuthentication`.
- **Headless Flow**: Powered by `allauth-headless` for standardizing auth across providers.
- **JWT**: Custom RS256 token strategy using `JWT_PRIVATE_KEY` for secure, stateless communication.

```

## 🚀 Easy Distribution System (Phase 8)

The distribution system enables rapid sharing and tracking of polls via multiple channels.

- **Public Slugs**: Each poll has a unique, short, non-guessable slug generated via `shortuuid`.
- **QR Codes**: Generated on-demand with SVG/PNG support and Redis caching (1-day TTL).
- **Embedded Polls**: Iframe-based embedding support with canonical public URLs.
- **Analytics Tracking**: Asynchronous tracking using Celery and JSONB for:
    - `LINK_OPEN`: Direct access to public poll page.
    - `QR_SCAN`: Access via QR code.
    - `EMBED_LOAD`: Interaction through embedded iframes.
- **Social Sharing**: Enhanced metadata (OpenGraph & Twitter Cards) on public poll pages.
