---
name: review-design-docs
description: Use when the user asks to review design docs, check docs consistency, find gaps in requirements docs, or run a design-document review for this repo.
---

# Review design docs

## Overview

Run a structured review of this repository's design documents. Keep the parent agent's context small: delegate the heavy reading to the readonly subagent.

## Instructions for the parent agent

1. Do **not** open or skim the full `docs/` tree yourself.
2. Do **not** load `.cursor/skills/review-design-docs/references/checklist.md` into the parent context (the subagent reads it).
3. Launch the **design-doc-reviewer** subagent in the **foreground** (wait for completion).
4. Pass a Task prompt that includes all of the following:
   - Default review root: `docs/` (override only if the user named specific paths)
   - Any user focus areas (e.g. "API only", "auth flow")
   - Instruction to read `.cursor/skills/review-design-docs/references/checklist.md` first
   - Instruction to follow that checklist's severity/categories/output format exactly
   - Instruction: readonly — do not edit files; return findings only
5. When the subagent returns, present its findings to the user.
   - You may lightly reformat headings for readability.
   - Do **not** re-read the docs to second-guess or expand the review.
   - If the subagent failed, report the failure; do not silently fall back to a full parent-side review.

## When NOT to use

- Code review of `infra/`, `backend/`, or `frontend/` implementations
- Writing or rewriting design docs (use normal editing flow)
- One-line factual questions about a single known file (just answer; no full review)
