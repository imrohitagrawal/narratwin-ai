# Local Development

This guide explains how to work on NarraTwin AI before and after application code exists.

## Current repo state

The repo is currently in strategy/spec/quality-gate hardening mode. Do not expect backend or frontend commands to exist until Slice 1 implementation starts.

## Prerequisites

Recommended local tools:

```bash
brew install git gh python@3.12 node docker ripgrep ffmpeg
```

Recommended optional tools:

```bash
python3 -m pip install --upgrade pip uv
npm install -g npm
```

## Clone

```bash
git clone https://github.com/imrohitagrawal/narratwin-ai.git
cd narratwin-ai
git checkout main
git pull
```

## Branching

Use one branch per stage or vertical slice:

```bash
git checkout -b docs/stage0-prd-hardening
```

Use git worktrees only for parallel Codex tasks that touch different files:

```bash
git worktree add ../narratwin-stage1 stage1/architecture-hardening
```

Do not run two live Codex sessions against the same files in the same working tree.

## Environment

Copy the example env file only when implementation begins:

```bash
cp .env.example .env
```

Do not commit `.env` or real provider keys.

## Local quality commands

Preferred command:

```bash
make quality
```

If `make` is unavailable, run the closest applicable checks manually:

```bash
git status --short
git diff --check
```

Backend, frontend, and dependency-security wrappers are required only after code/manifests exist.

## Codex workflow

Use this order:

1. Ask Codex to read `AGENTS.md`.
2. Ask Codex to read `docs/AI_BUILD_BRIEF.md`.
3. Ask Codex to read `docs/SKILL_EXECUTION_PLAN.md` and `docs/SKILL_TRUST_REVIEW.md`.
4. Give Codex one issue or one stage only.
5. Require a short plan before edits.
6. Require changed-file summary after edits.
7. Run local gates.
8. Open a PR.

## Plan mode vs edit mode

Use planning/read-only mode for:

- repo audit
- PRD review
- architecture review
- skill trust review
- issue decomposition
- reviewer pass

Use edit mode only when:

- the current stage is approved
- files to touch are clear
- stop/go gates are known
- the task is scoped to one issue or slice

## Before pushing

```bash
git status --short
git diff --check
make quality
```

If a command is not available yet, document why it is not applicable.

## Recovery

If Codex starts broad scaffolding:

```bash
git status --short
git diff
```

Then revert unrelated files:

```bash
git restore <path>
```

If Codex adds secrets or unsafe files:

```bash
git restore <path>
```

Then rotate any exposed secret before continuing.

## First implementation target

Do not build avatar video first. Slice 1 is:

```text
project creation
→ markdown/text upload
→ ingestion/chunking/storage
→ retrieval
→ grounded walkthrough script
→ unsupported-claim evaluation
→ stored result
→ UI display
```
