# Swagger and OpenAPI guide

FastAPI generates Pace's OpenAPI document from route declarations. In local
development, the same document powers Swagger UI and ReDoc.

## Documentation endpoints

| Resource | Local URL | Purpose |
| --- | --- | --- |
| Swagger UI | `http://127.0.0.1:8000/docs` | Explore and call endpoints interactively |
| ReDoc | `http://127.0.0.1:8000/redoc` | Read a compact API reference |
| OpenAPI JSON | `http://127.0.0.1:8000/openapi.json` | Generate clients or validate the contract |

Set `PACE_DOCS_ENABLED=false` in a deployment environment to remove all three
routes. Health probes remain available when documentation is disabled.

## Authentication

Authenticated `/v1` operations accept the Supabase session access token:

```http
Authorization: Bearer <supabase-access-token>
```

The OpenAPI components include `BearerAuth` for this JWT. When an authenticated
route is implemented, declare that security dependency on the operation so
Swagger displays its lock icon. Do not paste service-role credentials or Plaid
tokens into Swagger.

## API conventions

- Product routes are mounted below `/v1`.
- Liveness and readiness probes are intentionally unversioned and unauthenticated.
- JSON is used for requests and responses.
- UTC timestamps use ISO 8601; date-only values use `YYYY-MM-DD`.
- Money is serialized as a decimal string.
- The backend derives the user ID from the verified JWT, never request data.
- `POST /v1/webhooks/plaid` is the exception to user JWT authentication and must
  validate Plaid webhook authenticity.

Errors use the Pace envelope:

```json
{
  "error": {
    "code": "TRACKED_ACCOUNT_REQUIRED",
    "message": "Select one account before continuing.",
    "details": {}
  }
}
```

Framework validation failures use `VALIDATION_ERROR` with field errors inside
`details.errors`. Route-specific responses should document their domain error
codes and status codes without returning sensitive diagnostics.

## Adding a documented route

1. Create a focused router module below `app/api/routes/`.
2. Define Pydantic request and response models rather than returning untyped maps.
3. Add `summary`, `description`, `response_model`, and expected error responses to
   each operation.
4. Include the module's router from `app/api/router.py`.
5. Add an HTTP contract test and inspect `/openapi.json` for the resulting schema.

The authoritative endpoint behavior remains
[`../../docs/API_REQUIREMENTS.md`](../../docs/API_REQUIREMENTS.md). Generated
OpenAPI describes implemented behavior; it must not be used to silently redefine
the product contract.

