# Authentication Guide

This application supports **dual authentication** for maximum flexibility:
- **Session-based** (cookies) - Traditional web browser clients
- **JWT tokens** - Mobile apps, SPAs, and API clients

## Authentication Flow

### 1. Session Authentication (Browser/Web)

**Login**:
```bash
curl -X POST http://localhost:8000/_allauth/browser/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

**Response**:
```json
{
  "meta": {"session_token": "abc123..."},
  "data": {"user": {"email": "user@example.com"}}
}
```

**Using Session**:
```bash
curl http://localhost:8000/api/v1/ai/generate-poll/ \
  -H "X-Session-Token: abc123..." \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a poll about movies"}'
```

---

### 2. JWT Authentication (API Clients)

**Login**:
```bash
curl -X POST http://localhost:8000/_allauth/app/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

**Response**:
```json
{
  "meta": {
    "access_token": "eyJ0eXAiOiJKV1QiLC...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLC..."
  },
  "data": {"user": {"email": "user@example.com"}}
}
```

**Using JWT**:
```bash
curl http://localhost:8000/api/v1/ai/generate-poll/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLC..." \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a poll about movies"}'
```

**Refresh Token**:
```bash
curl -X POST http://localhost:8000/_allauth/app/v1/auth/token/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJ0eXAiOiJKV1QiLC..."}'
```

---

## GraphQL Authentication

GraphQL supports both auth methods via headers:

### Session Token
```graphql
# Header: X-Session-Token: abc123...
mutation {
  generatePollFromPrompt(
    prompt: "Create a poll about favorite foods"
  ) {
    title
    questions
  }
}
```

### JWT Bearer Token
```graphql
# Header: Authorization: Bearer eyJ0eXAiOiJKV1QiLC...
mutation {
  generatePollFromPrompt(
    prompt: "Create a poll about favorite foods"
  ) {
    title
    questions
  }
}
```

---

## Configuration

### Environment Variables

**Development** (`.env`):
```bash
# Option 1: Use environment variable (recommended)
JWT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMII..."

# Option 2: Use file (fallback)
# Create config/jwt_private_key.pem and leave JWT_PRIVATE_KEY empty
```

**Production** (Render):
```bash
# REQUIRED: Set in Render dashboard
JWT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMII..."
```

### Generate JWT Key

```bash
# Generate and copy to clipboard
openssl genrsa 2048 | tr -d '\n'

# Or save to file for development
openssl genrsa -out config/jwt_private_key.pem 2048
```

---

## Token Lifetimes

- **Access Token**: 24 hours
- **Refresh Token**: 7 days

Configure in `config/settings/base.py`:
```python
HEADLESS_JWT = {
    "ACCESS_TOKEN_LIFETIME_MINUTES": 60 * 24,  # 24 hours
    "REFRESH_TOKEN_LIFETIME_HOURS": 24 * 7,  # 7 days
}
```

---

## Migration from Session-Only

If you're migrating from session-only authentication:

1. **No changes required** - Sessions still work
2. **New clients** can use JWT immediately
3. **Existing clients** continue using sessions

The `MultiAuthenticationBackend` tries all methods automatically.

---

## Google OAuth (Social Authentication)

### Setup

1. **Create OAuth Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create a new OAuth 2.0 Client ID
   - Add authorized redirect URIs:
     - `http://localhost:8000/_allauth/google/login/callback/` (development)
     - `https://yourdomain.com/_allauth/google/login/callback/` (production)

2. **Configure Environment Variables**:
   ```bash
   GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
   ```

### Usage

Users can sign up and log in using their Google account through the allauth UI at `http://localhost:8000/accounts/google/login/`.

---

## Security Best Practices

1. **Store JWT key securely**:
   - ✅ Environment variable in production
   - ✅ Never commit `config/*.pem` files
   - ✅ Rotate keys periodically

2. **HTTPS in production**:
   - JWT tokens transmitted in headers
   - Always use TLS/SSL

3. **Token refresh**:
   - Use refresh tokens for long-lived sessions
   - Access tokens auto-expire after 24h
