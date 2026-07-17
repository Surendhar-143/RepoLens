# Authentication & Session Security Guide

RepoLens uses a dual JWT token approach (Access + Refresh Tokens) alongside GitHub OAuth integrations.

## local Credentials Authentication
Local registers and logins are handled via the following endpoints:
* **Registration**: `POST /api/v1/auth/register` (takes email, password, username).
* **Login**: `POST /api/v1/auth/login` (checks password verify and returns JWT access & refresh tokens).

### Token Security Lifecycles
* **Access Tokens**: Short-lived (1 hour limit) sent in headers: `Authorization: Bearer <access_token>`.
* **Refresh Tokens**: Long-lived (30 days limit) sent via body parameters to `POST /api/v1/auth/refresh` to fetch new credentials when access expires.

---

## GitHub OAuth Integration
Users connect third-party repository lists through the following workflow:
1. Client initiates authorization request via: `GET /api/v1/github/connect?state=<local_jwt>`.
2. Backend redirects browser window to GitHub authorize gateway.
3. Upon approval, GitHub callbacks: `GET /api/v1/github/callback?code=<code>&state=<jwt>`.
4. Backend matches state, queries GitHub user profiles, inserts `github_accounts` credentials, and redirects back to web dashboard settings.
