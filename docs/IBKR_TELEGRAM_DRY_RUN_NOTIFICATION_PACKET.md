# IBKR Telegram Dry-Run Notification Packet

## Purpose

Phase 337-352 adds a Telegram dry-run notification packet on top of the local IBKR daily research pipeline. It converts:

- `ibkr_daily_operator_packet.csv`
- `ibkr_daily_research_pipeline_summary.csv`
- `ibkr_local_daily_runner_summary.csv`

into:

- `ibkr_telegram_notification_packet.csv`
- `reports/ibkr_telegram_notification_packet_report.md`
- `reports/ibkr_telegram_message_preview.md`

The message preview is operator-readable text that can be copied manually. It is not sent by the system.

## Why This Phase Does Not Send Telegram

This phase only validates the notification shape and safety markers. It does not read Telegram credentials, does not access the network, and does not call any Telegram API. Real sending is reserved for a later explicit gate where secrets and approval rules can be reviewed separately.

## Notification Status And Severity

| source operator status | notification_status | notification_severity |
|---|---|---|
| `OPERATOR_REVIEW_READY` | `READY_TO_NOTIFY` | `INFO` |
| `OPERATOR_REVIEW_BLOCKED` | `BLOCKED_NOTIFY` | `WARNING` |
| `SAFETY_REJECTED` | `SAFETY_REJECTED_NOTIFY` | `CRITICAL` |

`delayed_reference` messages explicitly identify delayed/reference-only context. `stale_reference` messages identify stale or delayed_frozen/reference-only context. `no_price`, `unsupported`, and `no_go` messages state that no action is allowed.

## Message Preview Format

`reports/ibkr_telegram_message_preview.md` contains one section per symbol:

- message title
- symbol
- notification status and severity
- final decision label
- research bucket
- usable reference price
- operator instruction
- safety line with `action_allowed=false` and `telegram_send_triggered=false`

## Local Runner Usage

Default local runner behavior is unchanged:

```bash
bash scripts/ibkr_local_daily_runner.sh
```

Enable the optional dry-run notification packet with:

```bash
bash scripts/ibkr_local_daily_runner.sh --telegram-dry-run
```

When enabled, the runner archives the notification CSV, report, and message preview into the run directory.

## Safety Boundary

- `action_allowed=false`
- `telegram_send_triggered=false`
- `broker_execution_triggered=false`
- `historical_data_request_triggered=false`
- `account_read_triggered=false`
- `position_read_triggered=false`
- `manual_review_required=true`
- no Telegram token read
- no chat id read
- no Telegram send
- no external network request
- no broker execution
- no historical data request
- no account or position reads

## Next Phase Handoff

Phase 353-368 may add a Telegram send gate, a secret template, and explicit send approval. Real send behavior must remain disabled unless that later phase defines and validates an explicit approval path.
