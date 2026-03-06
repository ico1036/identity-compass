---
name: company-fit-research
description: Research a target company and convert hiring signals into resume edits. Use when tailoring resumes per company by analyzing recent job descriptions, team needs, and role language; outputs company_fit_brief and resume_delta for downstream resume-ralph-loop validation.
---

# company-fit-research

Build a company-specific fit layer before resume rewriting.

## Inputs
- `--company` target company name
- `--jds-file` markdown/text file containing recent JD snippets (preferred)
- `--resume-file` current base resume markdown
- optional `--notes-file` additional company/team notes

## Outputs
- `company_fit_brief.md`: what the company appears to want now
- `resume_delta.md`: exact bullet/summary edits to apply
- `fit_signals.json`: scored keyword and theme signals

## Workflow
1. Aggregate company signals from JD text and notes.
2. Extract top demand themes (skills, team style, seniority, domain).
3. Compare against current resume text.
4. Produce concrete edit plan (replace/add/remove bullets).
5. Hand off edited resume to `resume-ralph-loop` for quality gate.

## Rules
- Keep claims evidence-grounded; do not invent ownership.
- Prefer role-fit language over generic self-praise.
- If signal confidence is low, mark assumptions explicitly.

## CLI example
```bash
python3 skills/company-fit-research/scripts/company_fit_research.py \
  --company "GIC" \
  --jds-file skills/obsidian-resume-brain/outputs/gic_jds.md \
  --resume-file skills/obsidian-resume-brain/outputs/master_resume_v2.md \
  --out-dir skills/obsidian-resume-brain/outputs/company-fit/gic
```

## TODO (next iteration)
- [ ] Add web fetch helper for company/team signals (news, careers pages).
- [ ] Add weighted scoring by recency and JD seniority.
- [ ] Add anti-fit detector (execution-heavy / low-latency mismatch).
- [ ] Add direct patcher that rewrites markdown resume automatically.
- [ ] Add one-command pipeline into resume-ralph-loop.
