# Git Hygiene Guide

## 1. Purpose

This guide defines safe Git usage for Precious_Metals_Monitor.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Never use git add .

Avoid:

    git add .

Use targeted staging only.

Example:

    git add docs/example.md scripts/example.sh

## 3. Do not commit local runtime files

Do not commit:

- config.yaml
- .venv/
- generated CSV logs
- generated Markdown reports
- local data snapshots
- credentials
- tokens
- account IDs

## 4. Check status before commit

Always run:

    git status --short

Before committing, confirm only the intended files are staged.

## 5. Clean generated artifacts

After running tests:

    ./scripts/cleanup_generated_artifacts.sh

Then check:

    git status --short

Expected local-only state may include:

    M config.yaml
    ?? .venv/

## 6. Staging rule

Only stage files related to the current phase.

Example:

    git add .gitignore scripts/cleanup_generated_artifacts.sh docs/GENERATED_ARTIFACT_CLEANUP.md docs/GIT_HYGIENE_GUIDE.md docs/MVP_V1_LOCAL_STATE_POLICY.md

## 7. Commit rule

Commit messages should clearly identify the phase and scope.

Example:

    Add Phase 42 generated artifact cleanup and git hygiene

## 8. Safety boundary

Git hygiene must preserve:

- no trading code changes
- no broker execution changes
- no Telegram real-send change
- no scheduler deployment change
- no config secret commit
