# AI GraphQL Integration Test

This document outlines how to test the AI-powered poll insights feature.

## Prerequisites

1. **API Keys**: Add to your `.env` file:
   ```env
   OPENAI_API_KEY=your_openai_key_here
   GEMINI_API_KEY=your_gemini_key_here  # Optional fallback
   ```

2. **Restart Docker**: After adding API keys:
   ```bash
   docker-compose restart web
   ```

## Available GraphQL Operations

### 1. Ingest Poll Data (Mutation)

### REST API Alternative

All AI features are also available via REST API at `/api/v1/ai/`:

#### 1. Generate Poll from Prompt (POST)
```bash
curl -X POST http://localhost:8000/api/v1/ai/generate-poll/ \
  -H "X-Session-Token: YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a poll about favorite programming languages"}'
```

#### 2. Generate Insight (POST)
```bash
curl -X POST http://localhost:8000/api/v1/ai/insights/generate/ \
  -H "X-Session-Token: YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"poll_id": 1, "query": "What are the trends?"}'
```

#### 3. Ingest Poll Data (POST)
```bash
curl -X POST http://localhost:8000/api/v1/ai/ingest/ \
  -H "X-Session-Token: YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"poll_id": 1}'
```

#### 4. Get Insight History (GET)
```bash
curl -X GET http://localhost:8000/api/v1/ai/insights/history/1/ \
  -H "X-Session-Token: YOUR_SESSION_TOKEN"
```

---

## GraphQL Operations

### 1. Ingest Poll Data (Mutation)
Converts poll data into vector embeddings for AI analysis.

```graphql
mutation {
  ingestPollData(pollId: 1)
}
```

**Expected Response**:
```json
{
  "data": {
    "ingestPollData": "Successfully ingested poll 1 data into vector store"
  }
}
```

### 2. Generate Poll Insight (Mutation)
Ask questions about poll data using natural language.

```graphql
mutation {
  generatePollInsight(
    pollId: 1
    query: "What are the most popular options in this poll?"
  ) {
    query
    insight
    provider
  }
}
```

**Expected Response**:
```json
{
  "data": {
    "generatePollInsight": {
      "query": "What are the most popular options in this poll?",
      "insight": "Based on the poll data, option 'Python' has 45 votes...",
      "provider": "openai"
    }
  }
}
```

### 3. Generate Poll from Prompt (Mutation) **NEW!**
Create a complete poll structure using AI - just describe what you want!

```graphql
mutation {
  generatePollFromPrompt(
    prompt: "Create a poll about favorite programming languages for web development"
  ) {
    title
    description
    questions
    provider
  }
}
```

**Expected Response**:
```json
{
  "data": {
    "generatePollFromPrompt": {
      "title": "Favorite Programming Languages for Web Development",
      "description": "Help us understand which languages developers prefer...",
      "questions": [
        {
          "text": "Which language do you use most for backend development?",
          "question_type": "SINGLE_CHOICE",
          "options": [
            {"text": "Python"},
            {"text": "JavaScript/Node.js"},
            {"text": "Java"},
            {"text": "Go"}
          ]
        }
      ],
      "provider": "openai"
    }
  }
}
```

### 4. Poll Insight History (Query)
Retrieve past AI insights for a specific poll.

```graphql
query {
  pollInsightHistory(pollId: 1) {
    id
    query
    response
    providerUsed
    createdAt
  }
}
```

### 5. Analytics Dashboard (Query) **NEW!**
Retrieve aggregated statistics, trends, and top polls.

```graphql
query GetAnalytics {
  analyticsStats(period: "30d") {
    totalPolls
    totalViews
    avgResponseRate
    pollsChange
  }
  analyticsTrends(period: "30d") {
    pollCreation {
      date
      value
    }
  }
  topPolls(limit: 3) {
    title
    engagementScore
  }
}
```

### 6. Generate Analytics Insight (Mutation) **NEW!**
Generate a quick AI insight for the analytics dashboard context.

```graphql
mutation {
  generateInsight(pollId: 1, query: "Explain the response rate trend")
}
```
**Expected Response**:
```json
{
  "data": {
    "generateInsight": "The response rate has increased by 15% over the last week..."
  }
}
```

## Testing Workflow

1. **Create a Poll** (via existing polls API)
2. **Add Questions and Options**
3. **Cast Some Votes**
4. **Ingest Poll Data**:
   ```bash
   # GraphQL Playground at http://localhost:8000/graphql/
   mutation { ingestPollData(pollId: YOUR_POLL_ID) }
   ```
   ```
5. **Generate Insights**:
   ```graphql
   mutation {
     generatePollInsight(
       pollId: YOUR_POLL_ID
       query: "Summarize the voting trends"
     ) {
       insight
       provider
     }
   }
   ```
6. **Check Analytics**:
   ```graphql
   query {
     analyticsStats(period: "30d") {
       totalViews
       avgResponseRate
     }
   }
   ```

## Authentication

All AI mutations and queries require authentication. You can use either **session tokens** (recommended for browsers) or **JWT** (recommended for API clients).

### Option 1: Session Token (Browser)

1. **Log In**:
   ```bash
   curl -X POST http://localhost:8000/_allauth/browser/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "yourpassword123"}'
   ```
   **Response**: Extract `sessionToken` from the response.

2. **Use in Requests**:
   - **REST**: Header `X-Session-Token: abc123def456...`
   - **GraphQL**: Header `X-Session-Token: abc123def456...`

### Option 2: JWT (API/Mobile)

1. **Obtain Token**:
   ```bash
   curl -X POST http://localhost:8000/_allauth/app/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "yourpassword123"}'
   ```
   **Response**: Extract `access_token` from `meta`.

2. **Use in Requests**:
   - **REST**: Header `Authorization: Bearer eyJ0eXAi...`
   - **GraphQL**: Header `Authorization: Bearer eyJ0eXAi...`

## Error Scenarios

### No API Keys
```json
{
  "errors": [{
    "message": "Failed to generate insight: No available LLM providers configured"
  }]
}
```
**Fix**: Add `OPENAI_API_KEY` or `GEMINI_API_KEY` to `.env`

### Poll Not Found
```json
{
  "errors": [{
    "message": "Failed to generate insight: Poll with id X not found"
  }]
}
```

### Not Authenticated
```json
{
  "errors": [{
    "message": "Authentication required"
  }]
}
```
