# Troubleshooting

## 1. pytest: command not found

Symptom:

    zsh: command not found: pytest

Cause:

The virtual environment is not activated, or pytest is not available as a shell command.

Fix:

    source .venv/bin/activate
    python -m pytest -q

## 2. Test run creates CSV or Markdown files

Symptom:

After running tests, git status shows files such as:

- ibkr_smoke_log.csv
- historical_quality_gate_log.csv
- reports/latest_report.md
- reports/ibkr_smoke_report.md

Cause:

Some tests generate local reports or snapshots.

Fix:

Do not commit generated runtime artifacts unless the current task explicitly requires them.

Typical cleanup:

    git restore reports/ibkr_smoke_report.md
    rm -f conversion_factor_calibration_log.csv
    rm -f historical_quality_gate_log.csv
    rm -f ibkr_historical_fetch_log.csv
    rm -f ibkr_smoke_log.csv
    rm -f precious_metals_signal_log.csv
    rm -f theoretical_price_snapshot.csv
    rm -f upstream_factor_snapshot.csv
    rm -f reports/conversion_factor_calibration_report.md
    rm -f reports/historical_quality_gate_report.md
    rm -f reports/ibkr_historical_fetch_report.md
    rm -f reports/latest_report.md
    rm -f reports/theoretical_price_report.md
    rm -f reports/upstream_factor_report.md

Then verify:

    git status --short

## 3. config.yaml appears as modified

Symptom:

    M config.yaml

Cause:

Local runtime configuration differs from repository baseline.

Fix:

Do not commit config.yaml unless a task explicitly requires it.

Before staging, use targeted git add commands only. Do not use:

    git add .

## 4. .venv appears as untracked

Symptom:

    ?? .venv/

Cause:

The local Python virtual environment exists inside the project directory.

Fix:

Do not commit .venv/.

Use targeted git add commands only.

## 5. Accidentally stuck in heredoc prompt

Symptom:

Terminal shows:

    heredoc>

Cause:

A shell heredoc command was started but not closed.

Fix:

Press:

    Ctrl + C

Then use Python file-writing commands or smaller paste blocks.

## 6. Branch already exists

Symptom:

    fatal: a branch named ... already exists

Fix:

Switch to the existing branch:

    git switch <branch_name>

or create a new unique branch name.

## 7. Push asks for upstream

Symptom:

Git says the current branch has no upstream branch.

Fix:

    git push -u origin <branch_name>

## 8. Safety boundary

Any troubleshooting step must preserve:

- research-only
- read-only
- manual-only
- no auto trade

Do not add, enable, or test order execution paths as part of troubleshooting.
