# MVP v1.0 Next Phase Decision

## 1. Purpose

This document defines the decision point after MVP v1.0 documentation closure.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Current state after MVP v1.0

The project has completed:

- main research workflow
- report generation
- daily log output
- Telegram-ready text output
- scheduler stub
- release checklist
- documentation pack
- safety boundary documentation
- future deployment reviews

## 3. Available next paths

There are four possible next paths.

## 4. Path A: Manual daily operation hardening

Goal:

Make the project stable for daily manual use.

Possible phases:

- generated artifact cleanup policy
- .gitignore review
- one-command acceptance test
- daily manual run checklist
- report archive policy

Recommended if the priority is immediate personal use.

## 5. Path B: Telegram dry-run implementation

Goal:

Move from Telegram-ready text to a gated dry-run send model.

Possible phases:

- Telegram message builder review
- dry-run sender
- token environment variable gate
- send_allowed false by default
- no-trade assertion test

Recommended only after artifact cleanup and operation hardening.

## 6. Path C: Scheduler dry-run implementation

Goal:

Move from scheduler stub to dry-run scheduled report generation.

Possible phases:

- wrapper script
- logs/scheduler/
- dry-run scheduler command
- failure log
- no-trade assertion test

Recommended before real Telegram sending.

## 7. Path D: UI prototype

Goal:

Create a local personal dashboard.

Possible phases:

- static report index
- Streamlit local dashboard
- report viewer
- daily log viewer
- final trading plan viewer

Recommended after daily operation stabilizes.

## 8. Recommended next sequence

Recommended order after MVP v1.0:

1. Phase 42: Generated artifact cleanup and git hygiene
2. Phase 43: One-command operation acceptance pack
3. Phase 44: Manual daily operation checklist
4. Phase 45: Scheduler dry-run implementation
5. Phase 46: Telegram dry-run implementation
6. Phase 47: Telegram real-send gate review
7. Phase 48: Local launchd deployment
8. Phase 49: Log rotation and failure alert review
9. Phase 50: Cloud deployment decision

## 9. Not recommended immediately

Do not immediately jump to:

- real Telegram send
- real scheduler deployment
- live IBKR expansion
- UI full-stack app
- auto trade
- broker execution

## 10. Decision statement

The recommended next phase is:

    Phase 42: Generated artifact cleanup and git hygiene

Reason:

Tests currently generate local CSV and Markdown artifacts. Cleaning this workflow will reduce operational errors before adding real scheduler or Telegram behavior.
