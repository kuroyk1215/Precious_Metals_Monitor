# IBKR Local Daily Runner Scheduler Plan

## Dry-Run Local Runner

Run the local daily wrapper in default dry-run mode:

```bash
bash scripts/ibkr_local_daily_runner.sh
```

Default mode calls the one-command research pipeline without `--execute-market-data`. It does not connect to IBKR and does not request market data.

## Execution C

Execution C is explicit:

```bash
bash scripts/ibkr_local_daily_runner.sh --execute-market-data --market-data-type=auto
```

Only this flag passes `--execute-market-data` into `scripts/ibkr_daily_research_pipeline.sh`. The existing pipeline and snapshot gates still prevent trading, account reads, position reads, and historical data requests.

## Log Directory

Each run creates:

```text
logs/ibkr_daily/YYYYMMDD/RUN_ID/
```

The runner copies existing pipeline CSV and Markdown outputs into that run directory and writes:

- `ibkr_local_daily_runner_summary.csv`
- `ibkr_local_daily_runner_report.md`

## Retention

The default retention is 30 days:

```bash
bash scripts/ibkr_local_daily_runner.sh --retention-days=30
```

Rotation removes only date directories under the configured log root that are older than the retention window. Invalid retention values fall back to 30 days. Use `--no-rotate` to skip rotation.

## Scheduler Plan

Generate scheduler examples without installing anything:

```bash
bash scripts/ibkr_scheduler_plan.sh --hour=16 --minute=10
```

Outputs:

- `reports/ibkr_scheduler_plan_report.md`
- `docs/examples/com.kuroyk.ibkr-daily-runner.plist.example`
- `docs/examples/ibkr_daily_runner_cron.example`

The script does not call `launchctl`, does not write crontab, and does not install a scheduled task.

## Manual Use Of Examples

The launchd plist and cron file are examples only. Replace `PLACEHOLDER_PROJECT_ROOT`, review the command, and install manually only after operator approval.

## Safety Boundary

Default behavior:

- no IBKR connection
- no market data request
- no broker execution
- no historical data request
- no account reads
- no position reads
- `action_allowed=false`
- `manual_review_required=true`

The local runner archives research outputs and prepares an operator-facing packet. It does not generate or execute trades.

## Next Phase

Phase 337-352 can add Telegram dry-run and notification packet support around the archived operator packet.
