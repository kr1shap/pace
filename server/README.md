# Pace server

FastAPI foundation for the Pace iOS app. Product endpoints belong under `/v1`; the
service probes and generated API documentation live at the root.

## Requirements

- Python 3.13

## Set up

From the repository root:

```bash
python3 -m venv server/.venv
server/.venv/bin/python -m pip install -r server/requirements.lock
```

For editable package metadata and developer tools declared in `pyproject.toml`, use:

```bash
server/.venv/bin/python -m pip install -e 'server[dev]'
```

Copy `server/.env.example` to `server/.env` only when local overrides are needed.
Settings use the `PACE_` prefix and secrets must stay out of source control.

## Run

```bash
cd server
.venv/bin/uvicorn app.main:app --reload
```

Then open:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>
- Liveness: <http://127.0.0.1:8000/health>
- Readiness: <http://127.0.0.1:8000/ready>

See [`docs/swagger.md`](docs/swagger.md) for API documentation conventions and usage.

## Verify

```bash
cd server
.venv/bin/python -m pip check
.venv/bin/pytest
.venv/bin/ruff check .
```

## Structure

```text
server/
├── app/
│   ├── api/             # Versioned router and route modules
│   ├── core/            # Settings and cross-cutting error behavior
│   └── main.py          # Application factory and ASGI entry point
├── docs/                # Backend operations and API documentation
├── tests/               # HTTP contract tests
└── pyproject.toml       # Package metadata and direct dependency pins
```

Domain modules should be added by product area and included from
`app/api/router.py`. Do not expose Supabase service credentials, Plaid tokens,
transaction cursors, or client-selected user IDs through routes or logs.

