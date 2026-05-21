# Local Automation Dry-Run Pack

## 1. Purpose

This pack defines local dry-run automation for Precious_Metals_Monitor.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Scope

This phase adds local dry-run scripts only.

Allowed:

- validate local automation readiness
- validate scheduler dry-run paths
- validate Telegram dry-run content policy
- validate no-trade assertions
- write dry-run logs

Not allowed:

- real scheduler deployment
- real Telegram sending
- real IBKR live data expansion
- broker order execution
- automatic trading

## 3. Added scripts

- scripts/local_automation_dryrun.sh
- scripts/scheduler_wrapper_dryrun.sh
- scripts/telegram_dryrun_check.sh

## 4. Verification

Run:

    ./scripts/local_automation_dryrun.sh

Expected result:

- all required scripts exist
- acceptance check passes
- daily manual check passes
- scheduler wrapper dry-run passes
- Telegram dry-run check passes
- no-trade assertion remains intact

## 5. Safety boundary

This pack does not call broker execution and does not send Telegram messages.
