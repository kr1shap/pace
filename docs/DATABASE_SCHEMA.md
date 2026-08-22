# Pace database schema

## 1. Overview

Pace uses Supabase PostgreSQL. Supabase Auth owns identities in `auth.users`; application tables live in `public`.

The final MVP tables are:

1. `profiles`
2. `bank_connections`
3. `accounts`
4. `transactions`
5. `goals`
6. `user_quests`
7. `user_achievements`

There are intentionally no `quest_definitions`, `quest_events`, or `account_tracking_periods` tables. Quest and achievement catalogues live in FastAPI code. Goals and quests are independent and `user_quests` intentionally has no `goal_id`.

## 2. Relationships

| Parent | Child | Relationship | Delete behavior |
| --- | --- | --- | --- |
| `auth.users` | `profiles` | 1:1 | Cascade |
| `profiles` | `bank_connections` | 1:N historically; one open connection | Cascade |
| `bank_connections` | `accounts` | 1:N imported eligible accounts | Cascade |
| `accounts` | `transactions` | 1:N | Cascade |
| `accounts` | `user_quests` | 1:N historical snapshots | Cascade |
| `profiles` | `goals` | 1:N history; one active | Cascade |
| `profiles` | `user_achievements` | 1:N | Cascade |

Composite foreign keys include `user_id` to prevent cross-user parent references.

## 3. Table definitions

### 3.1 `profiles`

Extends `auth.users` with Pace state.

| Column | Type | Rules |
| --- | --- | --- |
| `id` | `uuid` | PK; FK to `auth.users(id)` |
| `display_name` | `text` | Nullable |
| `timezone` | `text` | Default `UTC` |
| `total_xp` | `integer` | Default 0; non-negative |
| `current_level` | `integer` | Default 1; positive; cached when XP changes |
| `current_streak` | `integer` | Default 0; non-negative |
| `longest_streak` | `integer` | Must be at least `current_streak` |
| `last_activity_date` | `date` | Nullable |
| `onboarding_step` | `text` | Default `WELCOME` |
| `onboarding_completed` | `boolean` | Default false |
| `created_at` | `timestamptz` | Default `now()` |
| `updated_at` | `timestamptz` | Maintained by trigger |

Indexes: primary key on `id`; no additional MVP index.

### 3.2 `bank_connections`

Backend-only Plaid Item and synchronization state.

| Column | Type | Rules |
| --- | --- | --- |
| `id` | `uuid` | PK |
| `user_id` | `uuid` | FK to `profiles(id)` |
| `plaid_item_id` | `text` | Unique |
| `encrypted_access_token` | `text` | Required; never returned to client |
| `institution_id` | `text` | Nullable |
| `institution_name` | `text` | Nullable |
| `transactions_cursor` | `text` | Nullable; saved only after all sync pages succeed |
| `status` | `text` | `active`, `login_required`, `error`, `disconnected` |
| `error_code` | `text` | Nullable |
| `sync_status` | `text` | `idle`, `pending`, `running`, `failed` |
| `sync_requested_at` | `timestamptz` | Nullable |
| `sync_started_at` | `timestamptz` | Nullable |
| `sync_error` | `text` | Nullable |
| `last_synced_at` | `timestamptz` | Nullable |
| `created_at` | `timestamptz` | Default `now()` |
| `updated_at` | `timestamptz` | Maintained by trigger |
| `disconnected_at` | `timestamptz` | Nullable |

Constraints and indexes:

- `UNIQUE(plaid_item_id)` for Plaid identity.
- `UNIQUE(id, user_id)` supports composite ownership foreign keys.
- `bank_connections_user_idx(user_id)` supports ownership and cascade operations.
- Partial unique `bank_connections_one_open_per_user_uidx(user_id) WHERE status <> 'disconnected'`.
- Partial `bank_connections_pending_sync_idx(sync_requested_at) WHERE sync_status IN ('pending','failed')`.

### 3.3 `accounts`

Stores eligible accounts imported from Plaid.

| Column | Type | Rules |
| --- | --- | --- |
| `id` | `uuid` | PK |
| `user_id` | `uuid` | Owner |
| `bank_connection_id` | `uuid` | Connection owner FK |
| `plaid_account_id` | `text` | Plaid account identity |
| `name` | `text` | Required |
| `official_name` | `text` | Nullable |
| `type` | `text` | `depository` or `credit` |
| `subtype` | `text` | `checking` or `credit card`, paired with type |
| `mask` | `text` | Nullable display suffix |
| `current_balance` | `numeric(14,2)` | Nullable |
| `available_balance` | `numeric(14,2)` | Nullable |
| `credit_limit` | `numeric(14,2)` | Nullable |
| `iso_currency_code` | `text` | Nullable |
| `balance_updated_at` | `timestamptz` | Nullable |
| `is_tracked` | `boolean` | Default false |
| `created_at` | `timestamptz` | Default `now()` |
| `updated_at` | `timestamptz` | Maintained by trigger |

Constraints and indexes:

- Composite FK `(bank_connection_id, user_id)` → `bank_connections(id, user_id)`.
- `CHECK` permits only `depository/checking` or `credit/credit card`.
- `UNIQUE(bank_connection_id, plaid_account_id)` for account upserts.
- `UNIQUE(id, user_id)` supports child ownership FKs.
- `accounts_user_idx(user_id)` supports ownership lookups.
- `accounts_connection_owner_idx(bank_connection_id, user_id)` covers the composite foreign key.
- Partial unique `accounts_one_tracked_per_user_uidx(user_id) WHERE is_tracked = true`.

### 3.4 `transactions`

Stores Plaid transaction state plus user review state.

| Column group | Columns | Notes |
| --- | --- | --- |
| Identity | `id`, `user_id`, `account_id`, `plaid_transaction_id`, `pending_transaction_id` | Unique per user and Plaid transaction |
| Money | `amount`, `iso_currency_code`, `unofficial_currency_code` | Preserve Plaid sign |
| Dates | `transaction_date`, `transaction_datetime`, `authorized_date`, `authorized_datetime` | Display authorization date first |
| Merchant | `name`, `merchant_name`, `merchant_entity_id`, `logo_url`, `website` | `name` required |
| Classification | `payment_channel`, `category_primary`, `category_detailed`, `category_confidence` | Payment channel is `online`, `in store`, or `other` |
| State | `pending`, `removed_at` | Removed rows retained but hidden |
| Pace overrides | `user_category`, `reviewed_at` | User category overrides Plaid category |
| Timestamps | `created_at`, `updated_at` | `updated_at` maintained by trigger |

Constraints and indexes:

- Composite FK `(account_id, user_id)` → `accounts(id, user_id)`.
- `UNIQUE(user_id, plaid_transaction_id)` supports idempotent upsert.
- `transactions_user_idx(user_id)` supports ownership checks.
- Partial Activity index on `(account_id, COALESCE(authorized_date, transaction_date) DESC, id DESC)` where not removed.
- Partial effective-category index on `(account_id, COALESCE(user_category, category_primary), transaction_date DESC)` where posted and not removed.
- Partial reviewed index on `(account_id, reviewed_at)` where reviewed, posted, and not removed.

Display rules:

```text
display_name = merchant_name ?? name
display_date = authorized_date ?? transaction_date
effective_category = user_category ?? category_primary
```

### 3.5 `goals`

Stores goal focus history.

| Column | Type | Rules |
| --- | --- | --- |
| `id` | `uuid` | PK |
| `user_id` | `uuid` | FK to `profiles(id)` |
| `focus_area` | `text` | One of four MVP focus areas |
| `selected_category` | `text` | Optional; primarily for `SPEND_LESS` |
| `status` | `text` | `active` or `closed` |
| `created_at` | `timestamptz` | Default `now()` |
| `closed_at` | `timestamptz` | Required exactly when closed |
| `updated_at` | `timestamptz` | Maintained by trigger |

Indexes:

- Partial unique `goals_one_active_per_user_uidx(user_id) WHERE status = 'active'`.
- `goals_history_idx(user_id, created_at DESC)`.

### 3.6 `user_quests`

Stores activated quest snapshots. Definitions remain in FastAPI.

| Column group | Columns | Notes |
| --- | --- | --- |
| Identity | `id`, `user_id`, `account_id`, `quest_type` | No `goal_id` |
| Snapshot | `title_snapshot`, `description_snapshot`, `category` | Preserves the wording active at activation |
| Progress | `target_value`, `current_value`, `progress_unit`, `currency_code` | Units: `count`, `currency`, `days` |
| Lifecycle | `status`, `starts_at`, `expires_at`, `completed_at`, `progress_updated_at` | Status: active/completed/expired/closed |
| Reward | `xp_reward`, `xp_awarded_at` | Award once |
| Timestamps | `created_at`, `updated_at` | `updated_at` maintained by trigger |

Constraints and indexes:

- Composite FK `(account_id, user_id)` → `accounts(id, user_id)`.
- Target, current progress, and XP are non-negative.
- Currency quests require `currency_code`.
- Completed state requires `completed_at`.
- XP award timestamp is allowed only for a completed quest.
- Partial `user_quests_active_idx(user_id, expires_at) WHERE status = 'active'`.
- `user_quests_history_idx(user_id, created_at DESC)`.
- `user_quests_account_idx(account_id)` supports account closure/deletion operations.

The maximum of three active quests cannot be enforced with a normal index. FastAPI must lock/check/insert within one database transaction.

### 3.7 `user_achievements`

| Column | Type | Rules |
| --- | --- | --- |
| `id` | `uuid` | PK |
| `user_id` | `uuid` | FK to `profiles(id)` |
| `achievement_type` | `text` | Backend catalogue key |
| `unlocked_at` | `timestamptz` | Default `now()` |

`UNIQUE(user_id, achievement_type)` supports both listing and idempotent unlocks.

## 4. RLS and grants

- Enable RLS on every public table.
- Authenticated users may select only their own non-secret rows.
- The client has no insert, update, or delete grants on Pace tables.
- `bank_connections` has no authenticated policy and no client grants.
- FastAPI performs domain writes with server-side credentials.
- RLS predicates use `(SELECT auth.uid()) = user_id` or the equivalent profile primary key.

Functions such as `handle_new_user()` may remain `SECURITY DEFINER` when required by an Auth trigger, but must not be callable as public RPCs:

```sql
REVOKE EXECUTE ON FUNCTION public.handle_new_user() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.handle_new_user() FROM anon, authenticated;
```

Apply the same rule to internal maintenance functions such as `rls_auto_enable()` when present.

## 5. Atomic operations

The following must run transactionally:

- selecting a tracked account and untracking the previous one;
- activating quests while enforcing three active slots;
- completing a quest, awarding XP, updating level/streak, and unlocking achievements;
- closing active quests when disconnecting or changing the tracked account; and
- processing each successful Plaid sync page set and cursor update.

## 6. Plaid synchronization rules

1. Read the stored cursor.
2. Fetch every `/transactions/sync` page.
3. Upsert added and modified transactions by `(user_id, plaid_transaction_id)`.
4. Set `removed_at` for removed transaction IDs.
5. Recalculate affected active quests from the qualifying transaction set.
6. Persist the new cursor only after all pages and database work succeed.

The same webhook, transaction page, or quest evaluation may be processed more than once without duplicating data or rewards.
