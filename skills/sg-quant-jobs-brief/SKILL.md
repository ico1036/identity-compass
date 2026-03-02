# sg-quant-jobs-brief

Nightly briefing skill for Singapore quant job openings.

## What it does
- Collects job postings from **LinkedIn** and **Glassdoor** only
- Filters to Singapore roles only
- Filters to quant researcher / quant trader (and close variants)
- Runs strict iterative quality gate (**Ralph-loop**)
- Produces markdown + JSON outputs for morning review

## Files
- `sg_quant_jobs_brief.py` — runner script
- `outputs/` — generated briefings

## Ralph-loop checks
Each iteration enforces:
1. Source whitelist (`linkedin.com`, `glassdoor.com`) only
2. Required fields present (`company`, `title`, `link`, `date_posted`, `source`)
3. Singapore location validity
4. Role validity (quant researcher / quant trader + close variants)
5. Freshness (<= 60 days)
6. Duplicate removal (`source + company + title`)
7. Confidence scoring (0.0–1.0)
8. Stop when no further removals or max iterations reached

Any item failing checks is rejected.

## Run
From workspace root:

```bash
python3 skills/sg-quant-jobs-brief/sg_quant_jobs_brief.py \
  --output skills/sg-quant-jobs-brief/outputs/brief-$(date +%F).md \
  --json-output skills/sg-quant-jobs-brief/outputs/brief-$(date +%F).json
```

## Cron-ready overnight example
Run daily at 02:10 AM:

```cron
10 2 * * * cd /Users/ryan/.openclaw/workspace && /usr/bin/python3 skills/sg-quant-jobs-brief/sg_quant_jobs_brief.py --output skills/sg-quant-jobs-brief/outputs/brief-$(date +\%F).md --json-output skills/sg-quant-jobs-brief/outputs/brief-$(date +\%F).json >> skills/sg-quant-jobs-brief/outputs/cron.log 2>&1
```

## Notes
- Script respects robots checks before fetching pages.
- If one source is blocked/unavailable, output is still generated from accessible source(s).
- If both are inaccessible, output still generated with zero-result summary and QA logs.
