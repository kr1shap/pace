# Pace API requirements

## 1. API boundary

FastAPI is the domain boundary for Pace. Supabase Auth handles sign-up and sessions; the iOS app sends its Supabase JWT to FastAPI for every authenticated endpoint.

Recommended prefix:

```text
/v1
```

The API derives `user_id` from the validated JWT. Client payloads must never select or override another user ID.

## 2. Conventions

### Authentication

```http
Authorization: Bearer <supabase-access-token>
```

`POST /v1/webhooks/plaid` is not user-authenticated. It must validate Plaid webhook authenticity and resolve the connection from the Plaid Item ID.

### Content and time

- JSON requests and responses use `application/json`.
- Timestamps are ISO 8601 UTC strings.
- Date-only transaction fields use `YYYY-MM-DD`.
- Money is serialized as decimal strings rather than binary floating-point numbers.
- Currency codes use Plaid's ISO or unofficial currency fields.

### Error shape

```json
{
  "error": {
    "code": "TRACKED_ACCOUNT_REQUIRED",
    "message": "Select one account before continuing.",
    "details": {}
  }
}
```

Expected statuses:

- `400` invalid state or malformed domain input
- `401` missing, expired, or invalid session
- `403` authenticated but not allowed
- `404` resource not found for the current user
- `409` state conflict or idempotency conflict
- `422` request validation failure
- `429` rate limited
- `502` upstream Plaid failure
- `503` temporarily unavailable or sync in progress

## 3. Authentication and profile

Supabase SDK handles sign-up, sign-in, password reset, refresh, and sign-out.

### `GET /v1/profile`

Returns profile, onboarding, XP, level, and streak state.

### `PATCH /v1/profile`

Mutable fields:

```json
{
  "display_name": "Krisha",
  "timezone": "America/Toronto"
}
```

The client cannot directly set XP, level, streaks, or onboarding completion.

### `DELETE /v1/users/me`

Required behavior:

1. authenticate the user again when required;
2. disconnect the Plaid Item;
3. delete Pace-owned data;
4. delete or schedule deletion of the Supabase Auth user; and
5. return `204` only when the operation is accepted successfully.

The operation must be safe to retry.

## 4. Bank connection and accounts

### `POST /v1/bank/link-token`

Creates a Plaid Link token for Transactions. Configure account filters for:

- `depository/checking`
- `credit/credit card`

Response:

```json
{
  "link_token": "link-sandbox-...",
  "expires_at": "2026-08-22T18:00:00Z"
}
```

### `POST /v1/bank/exchange-token`

Request:

```json
{
  "public_token": "public-sandbox-...",
  "institution": {
    "id": "ins_123",
    "name": "Sandbox Bank"
  }
}
```

Required behavior:

- exchange server-side;
- encrypt the access token before persistence;
- upsert the Plaid Item and eligible accounts;
- reject a second open connection;
- never return the access token; and
- return eligible account summaries for selection.

### `GET /v1/bank/connection`

Returns safe connection metadata, sync state, last synchronization time, and the tracked account summary. It never returns an encrypted token or cursor.

### `DELETE /v1/bank/connection`

Required behavior:

- call Plaid Item removal where possible;
- mark the connection disconnected while cleanup is in progress;
- delete the connection row after Plaid revocation, cascading its accounts,
  transactions, and account-linked quest rows;
- preserve historical profile XP and achievements; and
- return the product to a disconnected onboarding state.

### `GET /v1/accounts`

Returns only eligible imported accounts owned by the user.

### `POST /v1/accounts/{account_id}/track`

Selects the user's one tracked account.

Required transaction:

1. validate ownership and eligible type;
2. lock the user's account rows;
3. untrack the previous account;
4. close active quests tied to the previous account;
5. set the selected account as tracked; and
6. commit.

Response includes the tracked account and whether an initial transaction import is required.

## 5. Plaid synchronization

### `POST /v1/webhooks/plaid`

Handles Plaid transaction-update and Item-error events.

Requirements:

- verify webhook authenticity;
- locate the connection from `item_id`;
- mark sync requested or connection login-required/error state;
- acknowledge duplicate events safely; and
- never trust a user ID from webhook content.

### Synchronization algorithm

For a transaction update:

1. acquire a per-connection synchronization lock;
2. set `sync_status = running`;
3. page through Plaid `/transactions/sync` from the stored cursor;
4. upsert added and modified rows;
5. mark removed rows with `removed_at`;
6. recalculate affected active quest progress;
7. atomically complete newly satisfied quests and award XP once;
8. save the final cursor and `last_synced_at`; and
9. set `sync_status = idle`.

On failure, do not advance the cursor. Set `sync_status = failed` with a safe diagnostic message.

Opening Home must not run this algorithm. Home reads stored state only.

## 6. Transactions

### `GET /v1/transactions`

Query parameters:

| Parameter | Meaning |
| --- | --- |
| `cursor` | Opaque keyset-pagination cursor |
| `limit` | Page size with a server maximum |
| `category` | Effective category filter |
| `date_from` | Inclusive display-date lower bound |
| `date_to` | Inclusive display-date upper bound |
| `pending` | Optional pending-state filter |

Always use the tracked account. Sort by display date descending, then ID descending. Exclude `removed_at IS NOT NULL`.

Response item fields include:

```json
{
  "id": "uuid",
  "display_name": "Coffee Shop",
  "amount": "5.75",
  "currency_code": "CAD",
  "display_date": "2026-08-22",
  "effective_category": "FOOD_AND_DRINK",
  "plaid_category": "FOOD_AND_DRINK",
  "user_category": null,
  "pending": false,
  "reviewed": false,
  "logo_url": null
}
```

### `GET /v1/transactions/summary`

Returns tracked-account summaries for a requested period:

- total outflow;
- identifiable inflow;
- category totals;
- top purchases;
- fee-like transactions;
- transaction count; and
- coverage label explaining the tracked-account boundary.

Calculations include only posted, non-removed rows.

### `PATCH /v1/transactions/{transaction_id}/category`

Request:

```json
{
  "category": "GROCERIES"
}
```

An explicit `null` removes the override. After update, recalculate active quests affected by effective category.

## 7. Goals

### `POST /v1/goals`

Request:

```json
{
  "focus_area": "SPEND_LESS",
  "selected_category": "FOOD_AND_DRINK"
}
```

Reject creation when an active goal already exists. Validate whether the selected category is required or allowed for the focus area.

### `GET /v1/goals/current`

Returns the active goal and explainable tracked-account insights. It does not return a fabricated balance-progress percentage.

### `PATCH /v1/goals/{goal_id}`

Allows permitted edits, such as changing the selected category. Re-evaluate recommendations but do not mutate existing quest snapshots.

### `POST /v1/goals/{goal_id}/close`

Closes the goal and sets `closed_at`. It does not delete history and does not automatically close independent quests.

### `GET /v1/goals/history`

Returns newest-first active and closed goal records for the user.

## 8. Quests and game state

### `GET /v1/quests`

Returns active quest slots, recent completed/expired quests, and whether a replacement slot is open.

### `GET /v1/quests/recommendations`

Returns backend quest definitions transformed into user-specific candidates. Inputs may include:

- tracked-account transaction history;
- active goal focus;
- category coverage;
- recently completed quest types; and
- open quest slots.

The active goal is recommendation context only. Activated quests do not store `goal_id`.

### `POST /v1/quests/{quest_type}/activate`

Creates a user-specific snapshot with title, description, target, unit, timing, and XP reward.

Requirements:

- validate the quest type against the backend catalogue;
- validate the tracked account and required data;
- enforce at most three active quests under a lock;
- prevent duplicate activation when the quest type disallows it; and
- return `409 QUEST_SLOTS_FULL` when no slot is open.

### `GET /v1/quests/{quest_id}`

Returns the snapshot, progress, qualifying period, status, and a plain-language explanation of how progress is calculated.

### `POST /v1/quests/{quest_id}/check-in`

For manual quests only. Example purchase-review payload:

```json
{
  "reviews": [
    {
      "transaction_id": "uuid",
      "category": "GROCERIES"
    }
  ]
}
```

The backend validates ownership, marks transactions reviewed, applies permitted category overrides, recalculates progress, and performs completion/reward logic atomically.

### Completion transaction

When a quest first reaches its target:

1. lock the quest and profile;
2. return success without another reward if already completed;
3. set the quest completed state;
4. award XP and update cached level;
5. update streak state when eligible;
6. insert newly unlocked achievements with `ON CONFLICT DO NOTHING`; and
7. commit.

## 9. Dashboard, progress, and recaps

### `GET /v1/dashboard`

Returns one payload optimized for Home:

- tracked account summary;
- current-period tracked spending;
- identifiable income when supported;
- active quest preview and open-slot state;
- active goal card;
- XP and level;
- connection/sync status; and
- `last_synced_at`.

### `GET /v1/progress`

Returns XP, level, progress to the next level, streaks, achievements, and quest-history summaries.

### `GET /v1/recaps/{year}/{month}`

Returns a monthly recap scoped to the user's current tracked account. Include tracked-spending totals, category highlights, quest outcomes, and XP earned. Do not label the result as the user's complete finances.

The MVP does not preserve account-tracking periods. If the user changes the tracked account, financial recap calculations use the newly tracked account; quest history remains tied to each quest's stored `account_id` while that account row exists.

## 10. State transitions and errors

| Code | When |
| --- | --- |
| `BANK_CONNECTION_EXISTS` | User already has an open connection |
| `UNSUPPORTED_ACCOUNT_TYPE` | Returned or selected account is not eligible |
| `TRACKED_ACCOUNT_REQUIRED` | Financial feature accessed before selection |
| `PLAID_LOGIN_REQUIRED` | Item needs user repair |
| `SYNC_IN_PROGRESS` | Conflicting sync request |
| `GOAL_ALREADY_ACTIVE` | User tries to create a second active goal |
| `QUEST_SLOTS_FULL` | User already has three active quests |
| `QUEST_NOT_MANUAL` | Check-in attempted on an automatic quest |
| `TRANSACTION_NOT_FOUND` | Transaction is missing, removed, or not owned |
| `RESOURCE_STATE_CONFLICT` | Operation is incompatible with current lifecycle state |

## 11. API acceptance checks

- Cross-user IDs always behave as not found or forbidden.
- Secrets never appear in responses or logs.
- Replaying a Plaid webhook does not duplicate transactions or XP.
- Replaying quest completion does not award XP twice.
- No financial summary includes another account or a pending/removed transaction.
- Account selection, disconnection, and deletion preserve database invariants.
- Expired JWTs consistently return `401` and allow the client to refresh/retry once.
