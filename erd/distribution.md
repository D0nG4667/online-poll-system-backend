```mermaid
erDiagram
    %% Distribution Layer ERD
    %% Domain: Sharing, QR Codes, Embeds, Tracking

    Poll {
        int id PK
        string slug UK "Public Identifier"
    }

    DistributionAnalytics {
        int id PK
        int poll_id FK
        string event_type "LINK_OPEN, QR_SCAN, EMBED_LOAD, SOCIAL_SHARE"
        datetime timestamp
        string ip_address
        string user_agent
        string referrer
        jsonb metadata
    }

    PublicLink {
        string url "https://polls.plaudepolls.com/p/{slug}"
    }

    QRCode {
        binary image "Generated on fly (Redis cached)"
    }

    Embed {
        html code "Iframe snippet"
    }

    %% Relationships
    Poll ||--o{ DistributionAnalytics : "tracks"
    Poll ||--|| PublicLink : "accessed_via"
    Poll ||--|| QRCode : "scanned_via"
    Poll ||--|| Embed : "embedded_via"

    %% Rationale
    %% DistributionAnalytics: Granular tracking of how a poll is accessed (QR, Link, User Share).
    %% Virtual Entities (PublicLink, QRCode, Embed): Represent the distribution channels derived from the Poll slug.
```

## Rationale
- **DistributionAnalytics**: The central entity for tracking distribution performance. It captures the `event_type` (e.g., did they scan a QR code or click a link?), along with technical metadata (IP, User Agent) for fraud detection and analytics.
- **Virtual Entities**: `PublicLink`, `QRCode`, and `Embed` are not stored as database tables but are key logical components of the distribution system, generated dynamically based on the Poll's `slug`.
