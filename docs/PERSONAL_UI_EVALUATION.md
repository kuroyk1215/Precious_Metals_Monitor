# Personal UI Evaluation

## 1. Purpose

This document evaluates a future personal-use UI for Precious_Metals_Monitor.

Current boundary:

- research-only
- read-only
- manual-only
- no auto trade

Phase 40 does not implement a UI. It only evaluates possible UI directions.

## 2. Goal

The future personal UI should help the user review outputs more efficiently.

Allowed UI functions:

- show latest Markdown report
- show daily log
- show Telegram-ready text
- show final research trading plan
- show data status
- show scheduler status
- show manual review checklist
- trigger local research run in a future gated phase

Forbidden UI functions:

- place order
- cancel order
- rebalance
- send broker instruction
- trigger Telegram trade command
- bypass manual review

## 3. Candidate UI options

Candidate options:

- Streamlit local dashboard
- FastAPI backend plus simple web frontend
- React frontend plus Python backend
- static report viewer
- local-only command launcher

## 4. Recommended initial direction

Recommended order:

1. static report viewer
2. local Streamlit prototype
3. FastAPI backend review
4. React frontend only after data model stabilizes

Do not start with a complex full-stack app.

## 5. Minimum useful UI

A minimum useful UI should display:

- latest report
- latest daily log
- latest final research trading plan
- latest Telegram-ready text
- data_status summary
- run timestamp
- manual review checklist
- no-trade assertion

## 6. Manual review boundary

The UI must preserve manual review.

Required boundary:

    research-only / read-only / manual-only / no auto trade

## 7. Phase 40 non-goals

Phase 40 does not:

- write frontend code
- start a web server
- expose local API
- connect broker account
- add order buttons
- add Telegram command controls
- add scheduler deployment
