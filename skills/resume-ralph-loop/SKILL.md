---
name: resume-ralph-loop
description: Run a lightweight resume-vs-JD quality gate loop that scores keyword coverage, checks quantified achievements, flags generic writing, and surfaces consistency risks in JSON.
triggers:
  - "Evaluate this resume against a job description"
  - "Run resume quality gates"
  - "Check why my resume is weak for this JD"
  - "Generate a JSON diagnostics report for resume tailoring"
---

# resume-ralph-loop

Quality-gate scaffolding for resume tailoring iterations.

## What it does
- Accepts resume text and JD text (arguments or file paths).
- Produces JSON report with:
  - `keyword_coverage`
  - `quantified_achievements_present`
  - `genericness_heuristic`
  - `consistency_flags`
- Intended as a base loop to refine resume drafts before submission.

## Files
- `ralph_loop.py` — skeleton CLI analyzer script

## Example run
```bash
python3 skills/resume-ralph-loop/ralph_loop.py \
  --resume-file /path/to/resume.txt \
  --jd-file /path/to/jd.txt
```

## TODO (next iteration)
- [ ] Expand JD keyword extraction with phrase-level matching and weighting.
- [ ] Add STAR-bullet detection and scoring.
- [ ] Add hallucination-risk checks against verified resume-brain facts.
- [ ] Add iterative rewrite suggestions per failed gate.
- [ ] Support markdown/pdf ingestion and normalized text extraction.
