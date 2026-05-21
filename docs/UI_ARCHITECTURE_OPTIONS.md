# UI Architecture Options

## 1. Purpose

This document compares possible personal UI architectures.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Option A: Static report viewer

Description:

A simple local page or index that links to generated Markdown reports, logs, and Telegram-ready text.

Advantages:

- lowest complexity
- no server required
- low security risk
- easy to maintain

Limitations:

- limited interactivity
- no live refresh
- no run button

Recommended use:

- first UI milestone

## 3. Option B: Streamlit local dashboard

Description:

A local Python dashboard that reads generated outputs and displays them in a browser.

Advantages:

- fast to build
- good for tables and text
- Python-native
- suitable for personal use

Limitations:

- not ideal for complex frontend
- needs local server
- must avoid exposing secrets

Recommended use:

- first interactive prototype

## 4. Option C: FastAPI backend

Description:

A local API server that serves reports, logs, run status, and possibly triggers gated research runs.

Advantages:

- clean backend separation
- can support future React UI
- good for structured endpoints

Limitations:

- more engineering cost
- needs security boundary
- must block trading endpoints

Recommended use:

- later phase after static and Streamlit review

## 5. Option D: React frontend

Description:

A dedicated frontend for report reading, status panels, and charts.

Advantages:

- best UI flexibility
- good for long-term personal dashboard
- can support charts and filters

Limitations:

- highest complexity
- requires backend or static export
- more maintenance

Recommended use:

- after backend contract is stable

## 6. Recommended path

Recommended sequence:

1. static report viewer
2. Streamlit prototype
3. FastAPI local backend
4. React frontend if necessary

## 7. Forbidden UI elements

The UI must not include:

- buy button
- sell button
- cancel button
- rebalance button
- execute button
- broker order form
- Telegram trade command panel

## 8. Safety boundary

Every UI page should display:

    research-only / read-only / manual-only / no auto trade
