# Pace documentation

This directory is the durable product and engineering context for Pace.

| Document | Purpose |
| --- | --- |
| [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) | Product summary, architecture, vocabulary, constraints, and source-of-truth rules |
| [`PRD.md`](PRD.md) | Product purpose, MVP requirements, user journeys, acceptance criteria, and non-goals |
| [`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md) | PostgreSQL entities, fields, relationships, constraints, indexes, RLS, and transaction rules |
| [`API_REQUIREMENTS.md`](API_REQUIREMENTS.md) | FastAPI boundary, endpoints, payloads, errors, Plaid sync behavior, and domain update rules |
| [`FIGMA_UX_FLOWS.md`](FIGMA_UX_FLOWS.md) | Written screen-by-screen flows for onboarding, Home, goals, quests, Activity, progress, recaps, and Profile |

The repository-level [`AGENTS.md`](../AGENTS.md) is the concise instruction file for Codex and other coding agents.

## Source-of-truth policy

- Product intent and scope: `PRD.md`
- Data model and database invariants: `DATABASE_SCHEMA.md`
- HTTP contract and orchestration: `API_REQUIREMENTS.md`
- Screen behavior and navigation: `FIGMA_UX_FLOWS.md`
- Cross-cutting architecture and vocabulary: `PROJECT_CONTEXT.md`

When a decision changes, update every affected document in the same commit.
