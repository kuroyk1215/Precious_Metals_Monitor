# UI MVP Screen Spec

## 1. Purpose

This document defines a possible MVP screen layout for a future personal UI.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. MVP screen list

Recommended first screens:

1. Dashboard
2. Latest report
3. Daily log
4. Final research trading plan
5. Telegram-ready text
6. Data status
7. Scheduler status
8. Manual review checklist

## 3. Dashboard screen

Should display:

- latest run timestamp
- latest report status
- latest data status summary
- latest final research trading plan status
- scheduler mode
- Telegram mode
- no-trade assertion

## 4. Latest report screen

Should display:

- Markdown report
- report path
- generated timestamp
- data status warnings
- manual review reminder

## 5. Daily log screen

Should display:

- run history
- output status
- error status
- data availability notes
- report path

## 6. Final research trading plan screen

Should display:

- short-term view
- medium-term view
- long-term view
- rolling trade reference
- invalidation conditions
- risk triggers
- manual review checklist

## 7. Telegram-ready text screen

Should display:

- generated message text
- send status placeholder
- dry-run status
- manual copy option

It should not send real Telegram messages unless a later phase explicitly enables a gated send path.

## 8. Data status screen

Should display:

- instrument
- market
- data_status
- source_status
- timestamp
- fallback_method
- quality_note

## 9. Scheduler status screen

Should display:

- scheduler mode
- next planned run if configured
- last run status
- last error category
- log path

## 10. Forbidden screens

Do not add:

- order screen
- broker execution screen
- rebalance screen
- Telegram trading command screen
- margin management screen
