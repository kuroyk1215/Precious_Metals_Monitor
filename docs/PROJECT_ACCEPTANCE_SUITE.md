# Phase 74-76 Project Acceptance Suite

## 1. Purpose

This document defines the consolidated local acceptance suite for the project.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Acceptance goals

The acceptance suite should verify:

- Python syntax
- unit tests
- daily research run execution
- runtime output hygiene
- legacy runtime cleanup
- config.yaml staging protection
- active runtime trading API guard

## 3. Efficiency rule

Full unit tests should be run once at the suite level.

Nested checks should be used selectively to avoid unnecessary repeated test runs.

## 4. Required safety boundary

The suite must not trigger:

- broker execution
- real Telegram send
- real scheduler deployment
- automatic trading

## 5. Final boundary

The acceptance suite is a local validation tool.

It does not authorize unattended operation, external notification, broker connection, or trade execution.
