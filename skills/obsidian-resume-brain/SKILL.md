---
name: obsidian-resume-brain
description: Build and maintain an Obsidian-based resume knowledge graph from both explicit user inputs and ongoing conversation signals (strengths, decision style, tone, preferences, constraints). Use for identity-mapping before resume drafting, continuous evidence capture, and entropy-based readiness checks.
---

# obsidian-resume-brain

Maintain a graph-style, evidence-backed resume brain in Obsidian.

## Operating mode
- Default to **Identity Mapper mode** before drafting resumes.
- Do not start resume finalization until information gain flattens.
- Collect from two channels:
  1) explicit user-provided facts
  2) implicit conversation evidence (language, choices, tradeoffs, reactions)

## Always extract these fields from conversation
For each meaningful exchange, capture at least one item when available:
- `core_strengths` (repeatable edge, first-principles habits)
- `work_identity` (how user defines role/fit)
- `preferences` (domain/company/style)
- `anti_preferences` (what user wants to avoid)
- `decision_rules` (how user evaluates tradeoffs)
- `evidence_metrics` (numbers, scope, time horizon)
- `tone_profile` (aggressive/balanced/conservative language fit)
- `credibility_constraints` (no-overclaim boundaries)

## Storage layout
- `resume-brain/profile.md` (stable identity summary)
- `resume-brain/experience/*.md` (evidence blocks)
- `resume-brain/projects/*.md` (project proof)
- `resume-brain/signals/YYYY-MM.md` (conversation-derived traits)
- `resume-brain/entropy-log.md` (what changed today vs prior state)
- `job-pipeline/*.md` (target roles and fit notes)

## Update protocol (every meaningful session)
1. Append new conversation-derived signals to `signals/YYYY-MM.md`.
2. Update `profile.md` only when new evidence is repeat-confirmed.
3. Log delta in `entropy-log.md`:
   - New nodes added
   - Existing nodes strengthened
   - Contradictions found/resolved
4. Keep claim language grounded (`supported/contributed`) unless ownership is explicitly proven.

## Readiness gate for resume generation
Start resume drafting only when all are true:
- Core identity statements remain stable across multiple sessions.
- New conversations add mostly examples, not new identity nodes.
- Major contradictions are resolved.
- Target-role fit map is clear (priority + anti-targets + compensation constraints).

## Writing rule
Prefer short, evidence-linked statements over broad self-praise.
