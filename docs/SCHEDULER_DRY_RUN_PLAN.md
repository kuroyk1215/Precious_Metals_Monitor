# Phase 109-120 Scheduler Dry-run and Launchd Sample

## 1. Purpose

This document defines the local scheduler dry-run plan.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Goal

This phase generates scheduler planning artifacts only.

It does not install a scheduler, does not start a background job, and does not send any external notification.

## 3. Proposed JST schedule

| market | time_jst | workflow |
|---|---:|---|
| JP | 08:30 | pre-market research run |
| JP | 12:00 | midday research run |
| JP | 16:00 | post-close research run |
| US | 21:30 | pre-US research run |
| US | 01:00 | US session review |
| US | 05:15 | post-US research run |

## 4. Runtime outputs

Generated local artifacts:

- scheduler_dryrun_plan.csv
- reports/scheduler_dryrun_report.md

Committed sample artifact:

- examples/launchd_daily_research_run.sample.plist

## 5. Forbidden scope

This phase must not:

- install launchd jobs
- call launchctl
- write to ~/Library/LaunchAgents
- start background daemons
- send Telegram messages
- connect to IBKR
- request market data
- submit broker actions
- trigger automatic trading

## 6. Final boundary

Scheduler dry-run is planning only.

Actual scheduler deployment requires a separate explicit final gate.
