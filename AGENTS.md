# Pace repository instructions

This file is the entry point for Codex and other coding agents working in this repository. It is intentionally concise so it is loaded reliably at repository startup. Use it to route to the authoritative documents below rather than guessing product behavior from code or mockups.

## Codex startup routine

Before planning or editing:

1. Identify which product domains the request affects.
2. Read `docs/PROJECT_CONTEXT.md` first, then the authoritative document for each affected domain.
3. Inspect the existing implementation and migrations before proposing a change.
4. State any conflict between the request, implementation, and documentation; do not silently choose one.
5. Keep changes narrow and update affected documentation in the same commit.

## Required context

Read these documents in order:

1. [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md)
2. [`docs/PRD.md`](docs/PRD.md)
3. [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md)
4. [`docs/API_REQUIREMENTS.md`](docs/API_REQUIREMENTS.md)
5. [`docs/FIGMA_UX_FLOWS.md`](docs/FIGMA_UX_FLOWS.md)

For focused work, read only the documents needed after `PROJECT_CONTEXT.md`:

| Domain | Authoritative document |
| --- | --- |
| Product scope, behavior, acceptance criteria | `docs/PRD.md` |
| Tables, relationships, constraints, indexes, RLS | `docs/DATABASE_SCHEMA.md` |
| HTTP contracts, auth, errors, idempotency | `docs/API_REQUIREMENTS.md` |
| Screens, navigation, states, UX copy | `docs/FIGMA_UX_FLOWS.md` |

When documents disagree, stop and surface the conflict. The user-approved product decision is authoritative; after confirmation, update every affected document and implementation artifact together.

## Locked MVP decisions

- Pace is a read-only, money-habit-first iOS app. It does not move money or provide financial advice.
- The client is SwiftUI. The backend is FastAPI. Authentication and PostgreSQL are provided by Supabase. Financial data comes from Plaid Sandbox during development.
- A connected, onboarded user may have one open Plaid connection and exactly one tracked account.
- The tracked account must be either `depository/checking` or `credit/credit card`.
- All dashboard, insight, goal, quest, and recap calculations are scoped to the tracked account.
- Goals are long-lived focus areas. Quests are independent short-term actions. There is intentionally no `goal_id` in `user_quests`.
- Quest definitions and achievement definitions live in backend code, not database definition tables.
- The client never receives Plaid access tokens, Supabase service-role credentials, or transaction-sync cursors.
- Domain writes go through FastAPI. Multi-row operations must be atomic and idempotent.
- Do not introduce Kafka, Redis, a distributed queue, microservices, multiple tracked accounts, or money movement into the MVP.

## Implementation rules

- Preserve Plaid's amount sign: positive means money leaving; negative means money entering.
- Financial calculations exclude pending and removed transactions unless a feature explicitly displays them.
- Activity may display pending transactions, but must never display rows with `removed_at` set.
- Use `merchant_name ?? name`, `authorized_date ?? transaction_date`, and `user_category ?? category_primary` for display and filtering.
- Never compute XP awards, level changes, quest completion, and achievement unlocks in separate non-transactional writes.
- Never award XP twice. Treat Plaid syncs, quest check-ins, and webhook processing as retryable operations.
- Use non-shaming, scoped copy such as “tracked spending” rather than “all your spending.”
- For a tracked credit card, avoid “available cash” language.
- Add or modify indexes based on actual query patterns. Every foreign key should have a covering index unless an existing index has the same leading columns.
- Enable RLS on every table in an exposed schema. Revoke public execution from non-RPC `SECURITY DEFINER` functions.

## Repository conventions

- Treat this documentation as the baseline specification until executable code, migrations, and tests are added.
- Once commands exist, keep the canonical setup, lint, test, migration, and generation commands in this file.
- Prefer migrations over ad-hoc production SQL. Never rewrite an applied migration.
- Keep secrets in environment configuration. Commit example variable names only, never credentials or Plaid tokens.
- Add tests for changed business rules, synchronization behavior, authorization boundaries, and retry/idempotency paths.
- Do not add a dependency, service, or architectural layer unless the requirement cannot be met cleanly with the locked stack.
- Preserve backward compatibility for released API contracts and migrations unless a breaking change is explicitly approved.

## Change checklist

Before completing a change:

- Confirm it remains within MVP scope.
- Check authentication, ownership, RLS, and secret-handling implications.
- Check whether the API contract, schema, PRD, or UX-flow documents need updates.
- Test success, empty, loading, stale, retry, and error states where applicable.
- Run database advisors after schema changes.
- Run the narrowest relevant tests first, then the full available test/lint suite before handoff.
- Review the final diff for unintended product, schema, API, security, or copy changes.
- Do not silently change a locked product decision; call it out explicitly.
