# RC Manual Execution Rehearsal

## Purpose

Phase 401-416 prepares the first real Execution C operator workflow without executing it. The rehearsal generates a readiness packet, a report, and a command preview that the operator can review before manually copying any command.

## Why Execution Is Not Automatic

This phase must not run `--execute-market-data`. The flag is allowed only inside the command preview so the operator can inspect the exact command before deciding whether to run it outside this rehearsal.

The rehearsal does not connect to IBKR, request market data, send Telegram, read accounts, read positions, read funds, request historical data, or authorize trades.

## First Validation Universe

The first real Execution C validation should use GLD and SLV. These US ETFs are the preferred IBKR validation path for checking market data behavior and delayed/frozen fallback handling.

## Optional JP ETF Validation

1540.T and 1542.T remain optional JP ETF validation symbols. They are not the default core universe and should not lock the project into a Japan-only system.

## CN / 518880 Policy

518880.SH does not go through IBKR. China ETF coverage should use a manual market data adapter, CSV import, a non-IBKR source, or a future broker API adapter.

## Reading The Command Preview

The command preview is written to `reports/rc_execution_c_command_preview.md`. It contains manual commands only. The rehearsal script writes the preview and stops; it does not execute those commands.

Review the preview for:

- Execution C validation command
- local runner Execution C variant
- Telegram send gate command
- GLD / SLV first validation note
- JP optional ETF note
- 518880 excluded from IBKR note
- no-trade safety markers

## Local Config Gate

The rehearsal allows the normal local operator state where `git status --short` shows only:

```text
 M config.yaml
```

`config.yaml` must remain unstaged and local-only. The rehearsal blocks if `config.yaml` is staged, added, deleted, included in the cached diff, or if any other tracked or untracked file is changed. Local Telegram environment and approval files such as `.env.telegram*`, `telegram.env`, `telegram.env.local`, and `.telegram_send_approval*` must not be tracked.

## Manual Execution C

When the operator is ready, manually copy the Execution C command from the preview. The expected command shape is:

```bash
bash scripts/ibkr_execution_c_pipeline_validation.sh --execute-market-data --market-data-type=auto --telegram-dry-run
```

Only the operator should run this command. Codex and validation scripts must not run it automatically.

## Review After Manual Execution

After a manual Execution C run, review:

- `ibkr_execution_c_validation_packet.csv`
- `ibkr_daily_operator_packet.csv`
- `reports/ibkr_daily_operator_packet_report.md`
- `reports/ibkr_execution_c_validation_report.md`

All outputs remain research-only and manual-review-only.

## Stop And Roll Back

If any safety marker is not false, stop immediately and do not continue to Telegram send testing. Keep the local outputs for review, inspect the relevant report, and return to dry-run mode.

If the operator needs to discard local runtime outputs, remove only generated CSV/report/log files. Do not modify `config.yaml` unless the operator intentionally changes local configuration.

## Next Phase

Phase 417-432 may focus on first operator-run result ingestion and post-run analysis. That phase should consume the operator-run output files and summarize what happened without adding broker execution.
