# Pace Figma UX flows — written specification

## 1. Purpose

This document translates the Pace Figma flow maps into implementation-ready words. It defines screen intent, entry points, transitions, and required UI states.

The revised onboarding order in this document supersedes older sketches that placed goal selection before Plaid.

## 2. Global navigation and behavior

Authenticated users with completed onboarding enter a four-tab app shell:

1. **Home**
2. **Quests**
3. **Activity**
4. **Profile**

Global principles:

- Preserve the user's current tab when dismissing a sheet or detail view.
- Use navigation pushes for drill-down content and sheets for short selections, filters, and confirmations.
- Show a blocking reauthentication state only when the Supabase session cannot be refreshed.
- Show last-sync context when data may be stale.
- Keep mascots supportive and secondary to financial data.

## 3. Onboarding and authentication

### `ONB-01` — Welcome

**Purpose:** Introduce Pace's playful identity and core promise.

**Content:** Brand, mascot illustration, short value statement, primary “Get started” action, secondary “Sign in” action.

**Transitions:**

- Get started → `ONB-02`
- Sign in → `AUTH-03`

### `ONB-02` — Value introduction

**Purpose:** Explain that Pace turns tracked spending into goals and quests.

**Required message:** Pace is read-only and works from one selected spending account.

**Transition:** Continue → `AUTH-01`

### `AUTH-01` — Authentication choice

**Purpose:** Choose create account or sign in.

**Transitions:**

- Create account → `AUTH-02`
- Sign in → `AUTH-03`

### `AUTH-02` — Create account

**Inputs:** Email, password, confirmation, display name if required.

**States:** Inline validation, submitting, email already used, weak password, network error.

**Success:** Valid session → `ONB-03`.

### `AUTH-03` — Sign in and recovery

**Inputs:** Email and password. Include password-reset entry.

**States:** Invalid credentials, submitting, network error, reset confirmation.

**Success routing:**

- Completed onboarding → `HOME-01`
- Incomplete onboarding → the saved `onboarding_step`

### `ONB-03` — Connect account explanation

**Purpose:** Explain why Pace needs transaction access and what it will not do.

**Copy requirements:**

- Pace reads transactions but cannot move money.
- Pace supports one main chequing account or credit card.
- Goals, quests, and recaps will use only the selected account.

**Transitions:**

- Connect securely → `ONB-04`
- Back → authentication/value flow as appropriate

### `ONB-04` — Plaid Link

**Purpose:** Launch Plaid Link with eligible account filters.

**States:** Requesting Link token, Plaid presented, user cancellation, Link error, Item login error.

**Success:** Exchange token and load eligible accounts → `ONB-05`.

### `ONB-05` — Select tracked account

**Purpose:** Select exactly one eligible account.

**Content:** Institution, account name, account kind, mask, and a one-account explanation.

Suggested copy:

> Pick your main spending account. Pace works best when you choose the account or card you use most often. Your goals, quests, and recaps will be based only on this account's transactions.

**States:**

- Multiple eligible accounts: single-selection list
- One eligible account: preselect but require confirmation
- No eligible accounts: explain chequing/credit-card limitation and offer reconnect
- Continue without selection: inline requirement message

**Transition:** Confirm selection → `ONB-06`.

### `ONB-06` — Importing transactions

**Purpose:** Cover initial account save and transaction import.

**Content:** Progress animation, mascot, plain-language status.

**States:** Importing, slower-than-expected, retryable error, Plaid login-required, successful import with or without transaction history.

**Success:** → `ONB-07`.

### `ONB-07` — Choose goal

**Purpose:** Choose one focus area after Pace knows the tracked-account context.

**Options:** Spend less, Save more, Build awareness, Avoid fees.

**Behavior:** `SPEND_LESS` may request a category based on available transaction categories. Do not show balance targets.

**Transition:** Save goal → `ONB-08`.

### `ONB-08` — Choose three quests

**Purpose:** Select three recommendations from a card stack/list.

Each recommendation shows title, concise condition, duration, XP reward, and why it is available. Selection counter runs from `0/3` to `3/3`.

**States:** Loading recommendations, insufficient history fallback, selected, deselected, exactly-three validation.

**Transition:** Three selected → `ONB-09`.

### `ONB-09` — Confirm quest set

**Purpose:** Review the three quest cards and active goal before activation.

**Transitions:**

- Edit → `ONB-08`
- Start journey → activate quests atomically, complete onboarding, then `HOME-01`

## 4. Home and goals

### `HOME-01` — Home dashboard

**Information priority:**

1. tracked-account snapshot;
2. active quest preview;
3. goal card;
4. XP/level context;
5. last-sync state.

**Interactions:**

- Snapshot or Activity shortcut → `ACT-01`
- Quest preview → `QUEST-03`
- Goal card → `GOAL-01`
- XP/level → `PROG-01`

**Required variants:**

- Chequing: “Tracked account” and tracked spending language
- Credit card: “Tracked card” and card-spending language; never “available cash”

**States:** Skeleton loading, empty transactions, stale data banner, sync error, Plaid login required, open quest slot, no active goal.

### `HOME-02` — Disconnected/recovery Home

**Purpose:** Preserve access to the app shell when no usable bank connection exists.

**Content:** Clear connection state, what remains available, reconnect CTA. Do not show invented zero spending as if it were current data.

### `GOAL-01` — Goal detail

Shows focus area, selected category when present, relevant tracked-account insights, and plain-language habit guidance. It does not show balance-based completion progress.

**Transitions:**

- Edit → `GOAL-02`
- Close goal → `GOAL-03`

### `GOAL-02` — Edit goal

Allows permitted changes such as selected category. Explain that recommendations may change but active quests remain independent.

### `GOAL-03` — Close goal confirmation

Confirms that goal history is preserved and existing quests are not automatically deleted. Success returns to Home with a choose-new-goal card.

## 5. Quests, progress, and recaps

### `QUEST-01` — Quest journey

**Purpose:** Primary Quests tab and visual journey path.

Shows three active quest slots, completed journey nodes, upcoming replacement opportunities, and entry points to Progress and Recaps.

On appearance, fetch current quest state. If an automatic quest completed since the last visit, present `QUEST-05` before normal interaction.

**States:** Loading, three active, one or more open slots, no recommendations, offline/stale, retry error.

### `QUEST-02` — Quest recommendations

Opens only when a quest slot is available. Shows candidates with XP, duration, condition, and eligibility explanation.

Selecting a candidate opens `QUEST-03`; activation returns to `QUEST-01` with the slot filled.

### `QUEST-03` — Quest detail

Shows the immutable snapshot title/description, current and target progress, unit, dates, XP reward, status, and how qualifying activity is counted.

For manual purchase review, Start/Continue → `QUEST-06`.

### `QUEST-04` — Replace open quest slot

Appears after a quest is completed, expired, or closed. The old quest remains in history. Replacement uses recommendations and fills only the open slot.

### `QUEST-05` — Completion celebration

**Purpose:** Celebrate automatic completion when the user next opens Quests.

Shows completed quest, XP earned, possible level change, and newly unlocked achievements. Dismissal returns to `QUEST-01`, where the slot is now open for replacement.

The celebration must not trigger another XP award; it presents committed server state.

### `QUEST-06` — Weekly purchase review

Shows one of three purchases at a time as a swipeable review flow.

For each purchase, show merchant, amount, date, current category, and a category correction action. Submitting all reviews sends one quest check-in and then displays updated progress or completion.

**States:** Loading purchases, fewer than three eligible purchases, removed transaction during review, partial local progress, submit retry, completed.

### `PROG-01` — Progress overview

Shows level, total XP, progress to next level, current/longest streak, quest history summary, and achievement entry.

### `PROG-02` — Achievements

Shows unlocked achievements and locked placeholders only when the requirement can be explained without exposing hidden or misleading rules.

### `PROG-03` — Quest history

Filters or groups completed, expired, and closed quests. Tapping a row opens read-only `QUEST-03`.

### `RECAP-01` — Recap list

Lists available monthly recaps newest first. Empty state explains that a recap appears after sufficient tracked activity.

### `RECAP-02` — Monthly recap detail

Shows tracked spending, category highlights, notable purchases, quest outcomes, and XP earned. Every financial claim is scoped to the tracked account.

## 6. Activity

### `ACT-01` — Activity feed

Shows transactions grouped by display date, newest first, with cursor pagination.

Each row shows display name, amount, effective category, date context, and pending indicator.

**Interactions:**

- Filter → `ACT-02`
- Transaction → `ACT-03`
- Scroll end → fetch next cursor page with inline loader

**States:** Initial skeleton, empty account, no filter results, pending rows, stale banner, pagination retry, bank disconnected.

### `ACT-02` — Filters

Presented as a sheet.

**Category:** Effective categories available for the tracked account.

**Date presets:** This month, last month, last 30 days, custom range.

**Actions:** Apply, clear all, dismiss without changes. Show active-filter count on return to `ACT-01`.

### `ACT-03` — Transaction detail

Shows display/merchant name, amount, dates, pending state, payment channel, Plaid category, user override, and account mask.

**Transition:** Edit category → `ACT-04`.

### `ACT-04` — Change category

Single-selection category list. Saving applies the user override and returns to `ACT-03`; clearing restores the Plaid category. Refresh affected quest progress after success.

## 7. Profile

### `PROF-01` — Profile root

Shows profile header and sections for account, security, connected bank, privacy/data, and sign out.

### `PROF-02` — Account information

Allows display-name and timezone updates. Email changes remain governed by Supabase Auth flows.

### `PROF-03` — Password change

Starts the Supabase password-reset/update flow with success, expired-link, and retry states.

### `PROF-04` — Connected bank

Shows institution, connection health, last sync, eligible imported accounts, and the single tracked account. Includes reconnect/repair and disconnect entry points.

Changing the tracked account requires explicit confirmation because active quests tied to the old account will close.

### `PROF-05` — Disconnect confirmation

Explains that imported accounts, transactions, and account-linked quest rows will be removed while earned profile XP and achievements remain. Confirming returns to `HOME-02`.

### `PROF-06` — Privacy and data

Explains what Pace stores, the one-account boundary, read-only access, third-party providers, and account-deletion behavior.

### `PROF-07` — Delete account

Destructive confirmation requiring deliberate user acknowledgement. Show progress and retry-safe failure handling. Success clears the local session and returns to `ONB-01`.

### Sign out

Sign out clears local authentication/session state only. It does not disconnect Plaid or delete server data. Return to `AUTH-03`.

## 8. Cross-flow state rules

### Session expires

Attempt one Supabase refresh. If refresh fails, preserve non-sensitive navigation intent, clear sensitive cached content, and route to sign in.

### Plaid login required

Show a repair banner on Home and Connected Bank. Keep stored Activity visible with stale labeling where safe. Repair launches Plaid update mode.

### Data is stale

Show last successful sync time. Never replace stale values with zero.

### Unsupported account

Explain that Pace currently supports chequing accounts and credit cards only. Offer reconnect rather than exposing an unusable account.

### No transaction history

Allow onboarding to continue with generic awareness quests. Do not fabricate category insights.

### Reduced motion and accessibility

Celebrations and mascot animation must respect reduced-motion settings. Financial values, status, progress, and errors must not rely on color alone.
