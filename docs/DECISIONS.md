# Design decisions & constraints

The trade-offs that shape KRNL, and why they were made.

## 1. Message-ID dedup as the sync source of truth

Sync fetches the newest N emails and decides what's new by **`Message-ID`**, not by a
`last_synced_at` time window. A seen `message_id` is skipped before any extraction call, and a
partial unique index `(user_id, message_id)` is a hard guard at the DB. This makes re-syncs
idempotent and keeps the (rate-limited) extraction budget from being re-spent on mail already
processed.

## 2. Boost-only personalized priority

The Important tab could have used a pure relevance score, but that risks *hiding* genuinely
consequential mail a user didn't tag as interesting. Priority is therefore **boost-only**:

```
priority = max(importance, 0.4 · importance + 0.6 · relevance)
```

Interests can only lift an email's priority, never suppress it — a consequential notice still
surfaces even with zero interest matches, and a low-importance mail a user *does* care about
gets promoted. Users with no interests fall back to importance-only.

## 3. Extraction model & the rate-limit ceiling

All extraction, embeddings, and Ask KRNL answers run through **Google Gemini on a single shared
free-tier key**. The free tier's requests-per-day (RPD) is the binding constraint, not
throughput:

- Early on, the extraction model capped at **20 requests/day**, which a handful of test syncs
  exhausted (each sync = ~10 emails = ~10 calls). Switching to a lighter model raised this to
  **~500 RPD** on the same free key — enough for a small pilot, still a hard ceiling.
- Poll **frequency does not affect daily usage** (dedup means each email costs one call, ever),
  so auto-sync cadence is a free latency knob. The per-email `sleep` paces requests-per-minute;
  RPD is the wall.

**Scale path:** enable billing (RPD jumps by orders of magnitude) → lower the throttle. Past a
shared-key ceiling, isolate quota per user (see below).

## 4. Shared key vs. bring-your-own-key (BYOK)

Every user's calls flow through one shared key, so the whole pipeline serializes under one
global rate limit. **BYOK** (each user supplies their own Gemini key) would give each user their
own quota and fix cross-user fairness — but a *free* per-user key is still ~500 RPD, so BYOK
solves fairness, **not** single-user throughput. Only billing raises the per-key ceiling. The
project runs the shared-key model today for zero onboarding friction, with BYOK as a
documented scale option.

## 5. Concurrency & the throttle trap

The worker runs `concurrency=1`. The per-email `time.sleep` throttle only serializes calls
*because one task runs at a time* — it does **not** coordinate across worker processes. Raising
concurrency to N gives N parallel copies of the loop, each pacing itself → N× the request rate →
rate-limit errors. Any move past `concurrency=1` therefore requires first replacing the
per-task sleep with a **shared Redis token bucket** sized to the Gemini RPM; then concurrency
controls how many emails are in flight while the gate caps the true call rate.

## 6. Deadlines as naive IST wall-clock

Deadlines are stored as naive local (IST) wall-clock times, date-only or timed. This matches how
students read a deadline ("submit by 5 PM on the 8th") and keeps display and sorting intuitive.
The consequence: any time-window logic (e.g. the 24h reminder sweep) must compute in IST rather
than UTC.

## 7. Forward-only deadline merges

When an email extends an existing deadline, KRNL matches it to the original event (vector search
+ a confirmation check) and **moves the deadline forward only**, logging the change history —
rather than creating a duplicate event. Reminder-type follow-ups merge into the same event, so
one real deadline stays one row.

## 8. Privacy posture

Mail is connected with an **institute access token, never the LDAP password**; the token is
encrypted at rest (Fernet). App auth is Supabase (Google OAuth). Data is isolated per user. No
mail content is shared across users; vector search and answers are scoped to the requesting
user's own data.
