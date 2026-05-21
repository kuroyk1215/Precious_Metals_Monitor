# MVP v1.0 Local State Policy

## 1. Purpose

This document defines the expected local working tree state for MVP v1.0 operation.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Expected local-only files

The following may exist locally:

- config.yaml
- .venv/

These should not be committed as part of normal documentation or operation phases.

## 3. config.yaml policy

config.yaml may contain local runtime configuration.

It should not be included in normal phase commits unless a task explicitly requires it.

If config.yaml is modified locally, it may appear as:

    M config.yaml

This is expected.

## 4. .venv policy

.venv/ is the local Python virtual environment.

It should remain untracked.

If visible, it may appear as:

    ?? .venv/

This is expected.

## 5. Generated artifact policy

Generated CSV, Markdown report, and data snapshot files should not be committed unless a task explicitly requires them.

Use:

    ./scripts/cleanup_generated_artifacts.sh

## 6. Before creating a PR

Before every PR, verify:

    git status --short

Only the current phase files should be staged.

## 7. Safety boundary

Local state cleanup must not affect:

- trading logic
- IBKR safety boundary
- scheduler behavior
- Telegram behavior
- UI behavior
- broker execution
