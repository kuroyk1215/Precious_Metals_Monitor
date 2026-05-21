# Local Automation Acceptance Criteria

## 1. Purpose

This document defines acceptance criteria for local automation dry-run.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Acceptance criteria

Local automation dry-run is accepted if:

- scripts are executable
- MVP acceptance check passes
- daily manual check passes
- scheduler wrapper dry-run passes
- Telegram dry-run check passes
- tests pass
- generated artifacts can be cleaned
- config.yaml is not staged
- no trading code is changed

## 3. Rejection criteria

Reject the phase if:

- main.py is modified
- src/ is modified
- config.yaml is staged
- sample config enables auto trade
- sample config enables order action
- any script sends real Telegram messages
- any script calls broker execution
