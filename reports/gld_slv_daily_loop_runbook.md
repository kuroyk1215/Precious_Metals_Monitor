# GLD/SLV Daily Loop Runbook

## Scope

- GLD / SLV only.
- Research only, no automatic trading.
- No account, position, buying power, settled cash balance, or portfolio reads.
- No new markets and no new symbol universe.

## Daily Research Loop

Run the research loop into ignored runtime output:

```bash
scripts/batch1_gld_slv_core_research_loop.sh
```

Default outputs:

- `runtime/reports/latest_gld_slv_research.md`
- `logs/research_log_US.csv`

To refresh the tracked reference report intentionally, pass:

```bash
scripts/batch1_gld_slv_core_research_loop.sh --output-report reports/latest_gld_slv_research.md
```

## Dashboard

Generate the GLD/SLV dashboard into ignored runtime output:

```bash
scripts/gld_slv_dashboard_mvp.sh
```

Default output:

- `runtime/dashboard/index.html`

To refresh the tracked reference dashboard intentionally, pass:

```bash
scripts/gld_slv_dashboard_mvp.sh --output-html dashboard/index.html --report-path reports/latest_gld_slv_research.md
```

## Verification

Run the continuous verification layer:

```bash
scripts/verify_gld_slv_daily_loop.sh
```

The verifier checks:

- report exists
- `logs/research_log_US.csv` exists
- dashboard exists
- CSV header contains `action_rating`, `invalidation_level`, `risk_pct`, `confidence`, `action_allowed`
- GLD and SLV each have at least one row
- `no_price` rows have `NO_TRADE` and `action_allowed=false`
- dashboard contains GLD, SLV, `action_rating`, `data_delay_flag`, `US_30mEcho`, `IBKR cash account`, `settled cash`, and `GFV`
- active GLD/SLV daily loop files do not contain automatic trading API terms
- tracked generated reference files are not dirty

## Viewing Outputs

- Runtime report: `runtime/reports/latest_gld_slv_research.md`
- CSV log: `logs/research_log_US.csv`
- Runtime dashboard: `runtime/dashboard/index.html`
- Tracked reference report: `reports/latest_gld_slv_research.md`
- Tracked reference dashboard: `dashboard/index.html`

## Data Delay Flags

- `real_time`: normal research plan may be prepared, still research only.
- `delayed`: only WATCH or low-confidence C-level research; delayed data does not support strong action.
- `frozen`: reference only; no action.
- `no_price`: `NO_TRADE`, `action_allowed=false`, wait for valid quote.
- `source_conflict`: confidence downgraded, action rating no higher than WATCH, source conflict must be reviewed.

## Action Rating

- `A / B / C`: research-plan strength labels only; they are not order instructions.
- `WATCH`: observe and review; no strong action.
- `NO_TRADE`: do not trade; wait for valid data or risk reset.
- `action_allowed=false`: no actionable research plan is allowed.

## Git Hygiene

Daily runs should use runtime defaults, so `dashboard/index.html` and `reports/latest_gld_slv_research.md` are not modified.

If a legacy/manual command intentionally or accidentally refreshes tracked generated files, clean them with:

```bash
git restore dashboard/index.html reports/latest_gld_slv_research.md
```

Then rerun:

```bash
git status --short
```

## Expansion Gate

Expansion beyond GLD / SLV is allowed only after a separate approved batch explicitly changes the symbol universe, test scope, risk model, and dashboard scope. Until then, do not add A-shares, Japan ETFs, US stocks, scanner pages, full stock research pages, login, cloud deployment, or automated trading.
