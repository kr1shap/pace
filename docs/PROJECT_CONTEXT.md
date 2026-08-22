# Pace project context

## Product summary

Pace is a gamified personal-finance iOS app that helps users build awareness and improve everyday money habits. It combines transaction insights with goals, short-term quests, XP, levels, achievements, and monthly recaps.

Pace is a money-habit product first and a game layer second. It must be useful without making users feel judged, punished, or misled about the completeness of its financial view.

## MVP promise

Pace connects to one chequing account or one credit card through Plaid. It imports that account's transactions and uses them to:

- show a scoped financial snapshot;
- organize an Activity feed;
- recommend one active goal focus;
- recommend and track three active quests;
- award XP, levels, and achievements; and
- create lightweight progress summaries and monthly recaps.

Pace is read-only. It does not transfer funds, pay bills, initiate payments, trade, invest, lend, or provide financial advice.

## Technology stack

| Layer | Technology | Responsibility |
| --- | --- | --- |
| Mobile | SwiftUI | Native iOS UI, navigation, local presentation state, Supabase session handling |
| API | FastAPI / Python | Domain logic, authorization, Plaid integration, calculations, quest engine, writes |
| Authentication | Supabase Auth | Email/password identity and JWT issuance |
| Database | Supabase PostgreSQL | Durable user, connection, account, transaction, goal, quest, XP, and achievement state |
| Financial data | Plaid Transactions | Eligible account metadata and transaction synchronization |
| Design | Figma | Product flows, layouts, components, and visual direction |

The MVP intentionally does not use Kafka, Redis, a distributed job queue, a microservice architecture, or DynamoDB.

## System boundaries

### SwiftUI client

- Authenticates with Supabase Auth.
- Sends the Supabase access token to FastAPI as `Authorization: Bearer <jwt>`.
- Renders API response models and never contains server credentials.
- Launches Plaid Link using a short-lived Link token returned by FastAPI.
- Does not call Plaid directly for access-token exchange or transaction synchronization.

### FastAPI backend

- Validates the Supabase JWT and derives `user_id` from it; it never trusts a client-supplied user ID.
- Owns all domain writes and sensitive reads.
- Encrypts Plaid access tokens before persistence.
- Applies the tracked-account boundary to every financial calculation.
- Defines quest and achievement catalogues in code.
- Handles idempotent transaction sync and atomic game-state updates.

### Supabase

- `auth.users` is the identity source.
- `public.profiles` extends the Auth user.
- RLS is enabled on all public tables.
- The mobile client has no write grants on Pace tables.
- `bank_connections` is backend-only because it stores encrypted Plaid tokens and sync cursors.

### Plaid

- Development uses Plaid Sandbox.
- Link should filter to `depository/checking` and `credit/credit card` where supported.
- FastAPI must still revalidate returned account type and subtype.
- Plaid amount signs are stored unchanged.

## Core domain model

```text
auth.users
  └── profiles
       ├── bank_connections
       │    └── accounts
       │         ├── transactions
       │         └── user_quests
       ├── goals
       └── user_achievements
```

Goals and quests are deliberately independent in storage. A goal may influence which quests FastAPI recommends, but a quest does not belong to a goal and does not store `goal_id`.

## Locked vocabulary

| Term | Meaning |
| --- | --- |
| Tracked account | The one eligible chequing account or credit card used for all Pace calculations |
| Goal | A long-lived focus area: `SPEND_LESS`, `SAVE_MORE`, `BUILD_AWARENESS`, or `AVOID_FEES` |
| Quest | A time-bounded, measurable action stored as a user-specific snapshot |
| Quest recommendation | A backend-generated candidate based on transaction history and optionally the active goal |
| XP | Points awarded once when eligible actions or quests complete |
| Level | Cached user state derived from total XP and updated with XP changes |
| Achievement | A one-time unlock identified by `achievement_type` |
| Effective category | `user_category` when present, otherwise Plaid's `category_primary` |
| Display date | `authorized_date` when present, otherwise `transaction_date` |
| Removed transaction | A transaction retained for sync history but excluded from the product via `removed_at` |

## Product constraints

- One open Plaid connection per user.
- One tracked account per user.
- Eligible accounts are chequing and credit card only.
- One active goal per user.
- Up to three active quests per user.
- Transaction-derived calculations use posted, non-removed transactions from the tracked account.
- Opening Home reads stored data through `GET /dashboard`; it does not trigger Plaid.
- Changing the tracked account closes active quests tied to the previous account. Historical completed progress remains historical.
- The MVP has no account-tracking-period table. Financial recaps use the current tracked account.

## UX and content principles

- Light, playful, minimal, rounded, and character-driven.
- Mascots reinforce progress and guidance without obscuring financial information.
- Use clear, non-shaming copy.
- Explicitly state the one-account visibility boundary.
- Never imply Pace sees a user's complete financial life.
- Use “tracked spending,” “spending from this account,” or “card spending.”
- Keep error states actionable and preserve user progress whenever possible.

## MVP exclusions

- Multiple tracked accounts or multiple institution aggregation
- Savings, investment, loan, or mortgage tracking
- Plaid Auth or Liabilities
- Money movement or bill payment
- Financial, investment, tax, or credit advice
- Full budgeting and net-worth calculations
- Notifications
- Social features, leaderboards, or shared challenges
- Admin-authored database tables for quest or achievement definitions

## Data and security principles

- Store the minimum Plaid data required by the product.
- Never log access tokens, public tokens, authorization headers, or service-role credentials.
- User deletion must remove Pace data and disconnect the Plaid Item.
- Security-definer functions that are not public RPCs must have `EXECUTE` revoked from `PUBLIC`, `anon`, and `authenticated`.
- Database relationships must enforce ownership so one user's child row cannot reference another user's parent row.
- Retryable operations must be idempotent.

## Current repository status

The repository begins with documentation as the source of truth. Application code, deployment topology, package choices, and exact iOS architecture patterns should be added without contradicting the locked MVP decisions above.
