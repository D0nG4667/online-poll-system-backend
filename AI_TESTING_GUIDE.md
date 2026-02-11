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

## Testing Workflow

1. **Create a Poll** (via existing polls API)
2. **Add Questions and Options**
3. **Cast Some Votes**
4. **Ingest Poll Data**:
   ```bash
   # GraphQL Playground at http://localhost:8000/graphql/
   mutation { ingestPollData(pollId: YOUR_POLL_ID) }
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

## Authentication

All AI mutations and queries require authentication using **session tokens** (not JWT).

### How to Obtain a Session Token

1. **Sign Up** (if you don't have an account):
   ```bash
   curl -X POST http://localhost:8000/_allauth/browser/v1/auth/signup \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "yourpassword123",
       "password_confirm": "yourpassword123"
     }'
   ```

2. **Log In** to get your session token:
   ```bash
   curl -X POST http://localhost:8000/_allauth/browser/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "yourpassword123"
     }'
   ```

   **Response** (extract the `sessionToken`):
   ```json
   {
     "status": 200,
     "data": {
       "user": {"id": 1, "email": "user@example.com"},
       "sessionToken": "abc123def456..."
     }
   }
   ```

### Using Session Tokens

#### For REST API:
```bash
curl -X POST http://localhost:8000/api/v1/ai/generate-poll/ \
  -H "X-Session-Token: YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a poll about favorite programming languages"}'
```

#### For GraphQL:
In GraphQL Playground (`http://localhost:8000/graphql/`), add to HTTP Headers:
```json
{
  "X-Session-Token": "YOUR_SESSION_TOKEN"
}
```

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
