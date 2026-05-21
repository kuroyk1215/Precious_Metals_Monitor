# Report Archive Policy

## 1. Purpose

This document defines a report archive policy for manual operation.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Archive goal

Archive useful outputs for later review without committing runtime artifacts.

Recommended archived categories:

- Markdown reports
- daily logs
- Telegram-ready text
- final research trading plans
- run summaries
- failure records

## 3. Archive naming convention

Recommended naming pattern:

    YYYYMMDD_HHMMSS_<market>_<workflow>_<output_type>.<ext>

Examples:

    20260521_083000_JP_daily_report.md
    20260521_120000_JP_final_plan.md
    20260521_213000_US_telegram_ready.txt

## 4. Archive metadata

Each archived item should be traceable to:

- run timestamp
- market
- workflow
- config reference
- data status
- output type
- manual review status
- no-trade assertion

## 5. Git policy

Runtime archives should not be committed by default.

Commit only:

- documentation
- sample files
- scripts
- non-sensitive templates

Do not commit:

- private reports
- local logs
- account data
- broker output
- Telegram tokens
- private configs

## 6. Retention policy

Suggested personal retention:

- daily reports: keep as needed
- failure logs: keep until reviewed
- debug logs: short retention
- sensitive logs: avoid creating when possible

## 7. Safety boundary

Archived outputs remain research material only.

They are not:

- order tickets
- broker instructions
- automatic trading signals
- guaranteed entry or exit instructions
