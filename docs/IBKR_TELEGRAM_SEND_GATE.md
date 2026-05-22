# IBKR Telegram Send Gate

## Purpose

Phase 353-368 adds an explicit safety gate before any real Telegram delivery. It consumes the Telegram dry-run notification packet and message preview from Phase 337-352 and writes:

- `ibkr_telegram_send_gate_decision.csv`
- `reports/ibkr_telegram_send_gate_report.md`

## Default Behavior

The default mode is dry-run only. It does not read Telegram environment variables, does not read `config.yaml`, does not access the network, and does not send Telegram messages.

```bash
bash scripts/ibkr_telegram_send_gate.sh
```

Default output is `DRY_RUN_ONLY` with `telegram_send_triggered=false`.

## Local Env File

Use the committed placeholder only as a template:

```bash
cp docs/examples/telegram.env.example telegram.env.local
```

Edit the local copy outside git and load it into your shell before an intentional send test. Do not commit env files.

## Local Approval File

Use the committed placeholder only as a template:

```bash
cp docs/examples/telegram_send_approval.local.example .telegram_send_approval.local
```

Only create the local approval file when intentionally testing a real Telegram send. Do not commit approval files.

## Dry-Run Execution

Generate notification preview first:

```bash
bash scripts/ibkr_telegram_notification_packet.sh
```

Then run the send gate without sending:

```bash
bash scripts/ibkr_telegram_send_gate.sh
```

## Explicit Telegram Send

Real sending requires all of the following:

- `--send-telegram`
- `--approval-file` pointing to an existing local approval file
- `TELEGRAM_BOT_TOKEN` in the environment
- `TELEGRAM_CHAT_ID` in the environment
- `ibkr_telegram_notification_packet.csv`
- `reports/ibkr_telegram_message_preview.md`
- successful send gate validation

Example:

```bash
set -a
. ./telegram.env.local
set +a
bash scripts/ibkr_telegram_send_gate.sh --send-telegram --approval-file=.telegram_send_approval.local
```

The report and CSV redact token and chat id values.

## Runner Integration

Default runner behavior does not send Telegram and does not invoke the send gate:

```bash
bash scripts/ibkr_local_daily_runner.sh
```

To create the dry-run notification packet only:

```bash
bash scripts/ibkr_local_daily_runner.sh --telegram-dry-run
```

To run the explicit send gate:

```bash
bash scripts/ibkr_local_daily_runner.sh --telegram-send --telegram-approval-file=.telegram_send_approval.local
```

`--telegram-send` automatically generates the dry-run notification packet before entering the send gate.

## Status Fields

| field | values |
|---|---|
| `send_gate_status` | `DRY_RUN_ONLY`, `SEND_ALLOWED`, `SEND_BLOCKED`, `SEND_FAILED_SAFE` |
| `telegram_send_status` | `not_attempted`, `sent`, `failed`, `blocked` |
| `send_mode` | `dry_run`, `explicit_send` |
| `approval_file_status` | `not_required`, `present`, `missing` |
| `token_status` | `not_required`, `present`, `missing` |
| `chat_id_status` | `not_required`, `present`, `missing` |

## Safety Boundary

`action_allowed=false` is always preserved because Telegram delivery is notification transport only. It is not a trading authorization, broker instruction, account read, position read, or historical data request.

The send gate always writes:

- `action_allowed=false`
- `broker_execution_triggered=false`
- `historical_data_request_triggered=false`
- `account_read_triggered=false`
- `position_read_triggered=false`
- `manual_review_required=true`

## Next Phase Handoff

Phase 369-384 may validate the IBKR Execution C real delayed/frozen pipeline. Telegram sending remains separate from broker execution and must not be treated as trade authorization.
