# MVP v1.0 Manual Closure Acceptance

## 1. Purpose

This document defines the acceptance criteria for MVP v1.0 manual daily operation closure.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Closure criteria

MVP v1.0 manual closure is accepted if:

- MVP acceptance check passes
- daily manual check passes
- local automation dry-run passes
- deployment decision check passes
- local run archive check passes
- report archive dry-run passes
- retention validation check passes
- operation handoff check passes
- tests pass
- generated artifacts can be cleaned
- config.yaml is not staged
- no trading code is changed

## 3. Manual operation scope

Accepted manual operation includes:

- manual command execution
- manual report review
- manual data status review
- manual archive decision
- manual trade decision outside the system

## 4. Excluded scope

Still excluded:

- real scheduler deployment
- real Telegram send
- live IBKR expansion
- cloud deployment
- UI implementation
- automatic trading

## 5. Final boundary

MVP v1.0 manual closure means the project is ready for disciplined manual use.

It does not mean the project is ready for unattended 24h operation or automatic trading.
