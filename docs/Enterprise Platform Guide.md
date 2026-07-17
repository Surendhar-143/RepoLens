# Enterprise Platform Administration Guide

RepoLens Phase 9 transforms the platform into a production-ready, multi-tenant SaaS and self-hosted deployment capable of serving engineering organisations at scale.

---

## 1. Multi-Tenancy & Organizations

RepoLens supports isolated organizational workspaces.

### Creating an Organization
```
POST /api/v1/enterprise/organizations
{ "name": "Acme Engineering" }
```

* The creating user becomes **Owner** automatically.
* Organization members are stored in `organization_members` with roles: `owner`, `admin`, `member`.
* Every tenant operation is scoped by `organization_id`, enforcing data isolation at the row level.

---

## 2. Public REST API Authentication

RepoLens supports two authentication mechanisms for API consumers:

| Method | Header | Use Case |
|--------|--------|----------|
| JWT Bearer Token | `Authorization: Bearer <token>` | Interactive web sessions |
| API Key | `X-API-Key: rl_<hex>` | CLI, CI/CD, VS Code extension |

### Generating an API Key
```
POST /api/v1/enterprise/api-keys
{ "name": "GitHub Actions Key" }
```

> [!CAUTION]
> The raw token is returned **only once** at creation time. It is stored as a SHA-256 hash and cannot be retrieved again. Save it immediately.

### Revoking an API Key
```
DELETE /api/v1/enterprise/api-keys/{id}
```

---

## 3. Outbound Webhooks

Register endpoints to receive signed event payloads when repository events occur.

```
POST /api/v1/enterprise/webhooks
{
  "repository_id": "<uuid>",
  "target_url": "https://your.platform.com/hooks/repolens",
  "secret_token": "your_hmac_signing_secret"
}
```

Supported events delivered to target URLs:
* `analysis.completed` — Static scan finished
* `findings.generated` — Code quality or security findings created
* `documentation.updated` — Docs compiled or edited
* `health_score.changed` — Engineering health score recalculated

Payloads are signed using HMAC-SHA256. Verify with:
```python
import hmac, hashlib

def verify_signature(payload: bytes, secret: str, signature_header: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)
```

---

## 4. Audit Trail & Compliance

All security-relevant platform actions are recorded in the `audit_logs` table.

```
GET /api/v1/enterprise/audit
```

Tracked events include:
* `api_key.create` / `api_key.revoke`
* `webhook.register`
* `organization.create`
* `repository.analyze`
* `documentation.generate`

Logs capture: user ID, action name, IP address (where available), and structured metadata JSON.

---

## 5. CLI Usage

Install:
```bash
pip install repolens-cli
```

Authenticate:
```bash
repolens login --api-key rl_your_token_here
```

Common commands:
```bash
repolens analyze --repo <repo-id>         # Trigger static analysis
repolens findings --repo <repo-id>        # List quality findings
repolens search --repo <repo-id> "auth"   # Semantic search
repolens docs generate --type README      # Generate documentation
repolens export --repo <repo-id> --fmt json
```

---

## 6. VS Code Extension

Install from the VS Code Marketplace: **RepoLens AI Code Intelligence**

Features:
* Repository semantic search via Command Palette
* Inline AI explanations for selected code
* Architecture panel showing import graph
* Findings sidebar with code smell alerts
* Documentation lookup for any symbol

Configure with your API key in VS Code settings:
```json
{
  "repolens.apiKey": "rl_your_token_here",
  "repolens.apiUrl": "https://api.repolens.io"
}
```

---

## 7. Role-Based Access Control (RBAC)

| Role | Capabilities |
|------|-------------|
| **Platform Admin** | Full system access, user management |
| **Organization Owner** | All org resources, billing, member management |
| **Organization Admin** | Repositories, teams, webhooks, API keys |
| **Developer** | Analyze, search, chat, view findings |
| **Viewer** | Read-only access to all resources |
| **Auditor** | Audit log access, no write permissions |

---

## 8. Self-Hosted Deployment

RepoLens supports Docker Compose and Kubernetes deployments.

```bash
# Start full stack
docker compose -f docker-compose.prod.yml up -d

# Run migrations
docker compose exec api alembic upgrade head

# Scale workers horizontally
docker compose up --scale worker=4
```

Required environment variables:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@db/repolens
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
JWT_SECRET_KEY=<strong_random_key>
GITHUB_CLIENT_ID=<oauth_app_client_id>
GITHUB_CLIENT_SECRET=<oauth_app_secret>
```
