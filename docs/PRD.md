# Pace MVP product requirements document

## 1. Product overview

Pace is a read-only personal-finance habit app for iOS. It turns transaction awareness into small, approachable actions through goals, quests, XP, achievements, and recaps.

The product is intentionally scoped to one everyday spending account. That limitation must be presented clearly so users understand which transactions Pace can see.

## 2. Problem

Traditional finance apps can feel dense, judgmental, or overly focused on comprehensive budgeting. Users may know they want better money habits but lack small, concrete next steps.

Pace addresses this by:

- presenting a simple view of tracked spending;
- translating transaction patterns into short actions;
- making progress visible through a lightweight game layer; and
- avoiding claims that it represents a complete financial picture.

## 3. Product principles

1. **Habits before game mechanics.** Quests must represent useful financial-awareness actions.
2. **One clear data boundary.** All insights are based on the selected account or card.
3. **Read-only by design.** Pace never moves money.
4. **Explainable progress.** Users should understand which transactions changed a quest or insight.
5. **Non-shaming language.** Missed quests and spending changes are neutral information.
6. **Buildable MVP.** Prefer a cohesive SwiftUI/FastAPI/PostgreSQL implementation over infrastructure complexity.

## 4. Target user

The MVP targets a user who:

- uses one primary chequing account or credit card for everyday spending;
- wants awareness and manageable habit changes rather than a full budgeting system;
- benefits from visual progress and short challenges; and
- is comfortable connecting an account through Plaid.

## 5. MVP scope

### 5.1 Authentication

- Email/password sign-up, sign-in, password reset, sign-out, and account deletion through Supabase Auth.
- A Pace profile is created automatically after sign-up.
- Authentication is required before connecting Plaid.

### 5.2 Bank connection and account tracking

- Connect one Plaid Item.
- Import only eligible chequing and credit-card accounts.
- Require the user to select exactly one account to track.
- Explain that goals, quests, and recaps use only that account's transactions.
- Allow bank disconnection from Profile.
- Changing the tracked account is a later settings action, not part of everyday navigation.

### 5.3 Transactions and Activity

- Import and update Plaid transactions idempotently.
- Show transactions grouped by date.
- Show pending transactions with a visible pending state.
- Exclude removed transactions.
- Filter by category and date range.
- Allow a user category override.
- Support cursor pagination.

### 5.4 Goals

The user may have one active goal:

| Focus area | Meaning | Optional input |
| --- | --- | --- |
| `SPEND_LESS` | Reduce spending in one flexible category | `selected_category` |
| `SAVE_MORE` | Create more room for saving by improving spending habits | None |
| `BUILD_AWARENESS` | Review and understand spending patterns | None |
| `AVOID_FEES` | Notice and reduce avoidable fee-like transactions | None |

Goals are focus areas, not account-balance targets. They do not store saved amounts, starting balances, or exact progress balances.

Closing a goal preserves history. Goals are not deleted through the normal product flow.

### 5.5 Quests

- FastAPI generates quest recommendations from the tracked account's transaction history and may use the active goal as recommendation context.
- The user selects three quests during onboarding.
- The user may have at most three active quests.
- A completed or expired quest opens one replacement slot.
- Quest definitions live in backend code; activated quests store immutable title, description, target, unit, reward, and timing snapshots.
- Transaction-driven quests update after successful transaction synchronization.
- Manual quests update through an explicit check-in flow.
- Automatic completion is celebrated the next time the user opens Quests.
- XP is awarded once per completed quest.

Example MVP quest families:

- Review three purchases.
- Categorize a number of transactions.
- Stay below a category-spending threshold for a period.
- Complete a number of no-spend days for an eligible category.
- Identify or avoid fee-like transactions.

### 5.6 XP, levels, streaks, and achievements

- `total_xp` and `current_level` are cached in the profile and updated atomically.
- Levels are recalculated only when XP changes, not on every read.
- Achievements unlock once and are inserted idempotently.
- Streaks use the user's timezone and update from eligible activity.
- Progress, achievements, and recap entry points live under the Quests experience.

### 5.7 Home

Home shows, in priority order:

1. a tracked-account financial snapshot;
2. an active quest preview;
3. the active goal card;
4. XP/level context; and
5. last synchronization status.

Opening Home calls `GET /dashboard` and reads stored data. It does not call Plaid.

### 5.8 Recaps

- Show a lightweight monthly summary derived from posted, non-removed transactions.
- Include tracked spending, category highlights, quest results, and XP earned.
- Label all values as based on the selected account.
- Calculate financial recap values from the current tracked account; the MVP does not maintain separate account-tracking periods.

### 5.9 Profile and privacy

- View and edit Pace profile information.
- View the connected institution and tracked account.
- Disconnect the bank connection.
- Review privacy/data information.
- Delete the Pace account and associated data.
- Sign out without deleting server data.

## 6. Primary user journey

```text
Welcome
→ Value introduction
→ Create account or sign in
→ Connect Plaid
→ Select one eligible chequing account or credit card
→ Import transactions
→ Choose one goal
→ Choose three quests
→ Confirm
→ Home
```

## 7. Functional requirements

### Bank-data requirements

- Link must request Transactions and filter eligible account types where possible.
- The backend must reject unsupported returned account types.
- Plaid access tokens must be encrypted at rest.
- Sync must persist its cursor only after all returned pages succeed.
- Added and modified transactions are upserted by Plaid transaction ID.
- Removed transactions are marked with `removed_at`; they are not hard-deleted during sync.

### Calculation requirements

Unless explicitly displaying pending Activity rows, calculations must use:

```text
account_id = tracked_account_id
pending = false
removed_at is null
```

The user category override takes precedence over the Plaid category.

### Game-state requirements

- Quest progress can decrease if a modified or removed Plaid transaction changes the qualifying set before completion.
- Completed quests remain completed; the backend must not revoke already-awarded XP during ordinary Plaid corrections.
- Completion, XP award, level update, streak update, and achievement checks occur in one database transaction.
- At most three active quest rows may exist for a user.

### Security requirements

- Every API operation derives the user from the validated JWT.
- A user can access only their own rows.
- Sensitive bank-connection fields are backend-only.
- Public RPC execution is revoked from trigger and maintenance functions.
- Account deletion disconnects Plaid before or as part of deleting stored Pace data.

## 8. Required states

Every data-driven surface must define:

- initial loading;
- empty data;
- stale data;
- recoverable error with retry;
- authentication expiry;
- disconnected bank; and
- unsupported-account handling where applicable.

## 9. Success criteria for MVP

The MVP is complete when a test user can:

1. create an account and connect Plaid Sandbox;
2. select one eligible account;
3. import and browse transactions;
4. choose one goal and three quests;
5. see transaction-driven quest progress update idempotently;
6. complete a quest and receive XP exactly once;
7. view Home, Activity, Quests, Progress, Recap, and Profile flows;
8. disconnect Plaid and delete their account; and
9. complete these flows without exposing secrets or crossing user ownership boundaries.

## 10. Non-goals

- Complete budgeting or net-worth tracking
- Multiple tracked accounts
- Savings targets based on savings-account balances
- Credit-liability or loan payoff tracking
- Payments, transfers, investing, or financial recommendations
- Push notifications
- Social or competitive features
- Production bank coverage beyond Plaid-supported behavior

## 11. Deferred decisions

These are implementation choices, not permission to expand scope:

- Exact XP-to-level curve
- Exact quest catalogue and thresholds
- Exact achievement catalogue
- Deployment provider and durable sync-retry mechanism
- Analytics events and MVP success metrics
- Whether direct client reads remain enabled in production or all reads route through FastAPI
