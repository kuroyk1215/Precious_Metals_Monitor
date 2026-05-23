# Dashboard Output Manifest

## Scope

Phase 385-400 does not implement UI. It only keeps local outputs structured so a future dashboard can read them.

A future dashboard should read local files only. It must not place trades, cancel orders, read accounts, read positions, or directly request IBKR data. It does not read Telegram token, chat id, approval, or secrets files.

## CSV Inputs

`ibkr_market_data_snapshot.csv`

Market data snapshot rows for explicitly requested watchlist or universe symbols. This is a research input and not an execution instruction.

`ibkr_daily_integration_preflight.csv`

Daily integration preflight state, including whether required upstream files are present.

`ibkr_daily_integration_review_pack.csv`

Bridge review packet for daily integration outputs and safety markers.

`ibkr_final_research_review_pack.csv`

Final research review packet for manual operator review.

`ibkr_daily_operator_packet.csv`

Primary daily operator handoff file. A dashboard can treat this as the top-level operational summary.

`ibkr_telegram_notification_packet.csv`

Telegram dry-run notification packet. It is a preview and should not be interpreted as proof that a message was sent.

`ibkr_execution_c_validation_packet.csv`

Execution C validation packet. It records explicit market data validation status and keeps all trade-safety markers false.

`release_hardening_audit.csv`

Release hardening audit decision, including forbidden-call scan status, universe policy status, dashboard readiness, and release candidate status.

## Dashboard Safety Rules

- Read local CSV and report files only.
- Do not connect to IBKR.
- Do not send Telegram.
- Do not read credentials, token values, chat ids, approval files, or secrets.
- Display `action_allowed=false` as a hard safety boundary.
- Treat all rows as research-only and manual-review-only.
