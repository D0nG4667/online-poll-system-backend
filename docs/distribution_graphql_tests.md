# GraphQL Testing Queries for Distribution System

Use these queries at `http://localhost:8000/graphql/` to verify the distribution features.

### 1. Get Public Poll Detail (Anonymous)
```graphql
query GetPublicPoll($slug: String!) {
  publicPoll(slug: $slug) {
    id
    title
    description
    isOpen
    createdAt
  }
}
```
**Variables:**
```json
{
  "slug": "YOUR_POLL_SLUG"
}
```

### 2. Get Distribution Info (Links, QR, Embed)
```graphql
query GetDistributionInfo($slug: String!) {
  pollDistributionInfo(slug: $slug) {
    publicUrl
    qrCodeUrl
    embedCode
  }
}
```

### 3. Get Poll Distribution Analytics (Requires Auth)
*Note: Make sure to include the Authorization header or be logged in via session.*
```graphql
query GetPollAnalytics($slug: String!) {
  pollDistributionAnalytics(slug: $slug) {
    totalLinkOpens
    totalQrScans
    totalEmbedLoads
    recentEvents {
      eventType
      timestamp
      ipAddress
      userAgent
      referrer
    }
  }
}
```
