---
name: sg-quant-jobs-brief
description: Collect and summarize Singapore quant hiring roles using LinkedIn and Glassdoor only. Use for quant researcher/trader job scans, daily briefs, and shortlist generation with strict source/location filtering and chat-ready output.
---

# sg-quant-jobs-brief

Nightly briefing skill for Singapore quant job openings.

## What it does
- Collects job postings from **LinkedIn** and **Glassdoor** only
- Filters to Singapore roles only
- Filters to quant researcher / quant trader (and close variants)
- Runs strict iterative quality gate (**Ralph-loop**)
- Produces markdown + JSON outputs for morning review
- v2 adds anti-block strategy + optional browser fallback

## Files
- `sg_quant_jobs_brief.py` — runner script
- `outputs/` — generated briefings

## Strict constraints enforced
1. **Source strictness**: output links must be LinkedIn or Glassdoor domains only
2. **Region strictness**: `location` must match Singapore
3. **Roles strictness**: quant researcher/trader (+ close variants)

## v2 Collection Strategy
### Fast path (default)
- Requests/urllib collector
- Multiple query templates per site
- Pagination (`--max-pages`)
- Retries with exponential backoff + jitter
- Randomized user-agents

### Browser fallback (optional)
- Playwright sync API collector (`--use-browser`)
- Real navigation + wait/scroll behavior
- Optional visible browser mode (`--headful`)
- Longer navigation timeouts

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

## Run commands
From workspace root:

### 1) Fast path only (quick)
```bash
python3 skills/sg-quant-jobs-brief/sg_quant_jobs_brief.py \
  --output skills/sg-quant-jobs-brief/outputs/brief-$(date +%F).md \
  --json-output skills/sg-quant-jobs-brief/outputs/brief-$(date +%F).json \
  --max-pages 2 --max-rounds 2 --min-results 3
```

### 2) v2 unblock mode (recommended)
```bash
python3 skills/sg-quant-jobs-brief/sg_quant_jobs_brief.py \
  --output skills/sg-quant-jobs-brief/outputs/brief-$(date +%F)-v2.md \
  --json-output skills/sg-quant-jobs-brief/outputs/brief-$(date +%F)-v2.json \
  --max-pages 3 --max-rounds 4 --min-results 5 --use-browser
```

### 3) Headful debug mode (when blocked repeatedly)
```bash
python3 skills/sg-quant-jobs-brief/sg_quant_jobs_brief.py \
  --output skills/sg-quant-jobs-brief/outputs/brief-debug.md \
  --json-output skills/sg-quant-jobs-brief/outputs/brief-debug.json \
  --max-pages 2 --max-rounds 3 --min-results 5 --use-browser --headful
```

## Troubleshooting sequence (exact)
1. **Run fast path first** (command 1).
2. If result count is below target, run **v2 unblock mode** (command 2).
3. If still low/empty, run **headful debug mode** (command 3) and inspect page behavior.
4. If browser fallback logs `browser_unavailable`, install Playwright:
   ```bash
   python3 -m pip install playwright
   python3 -m playwright install chromium
   ```
5. Check generated markdown + JSON diagnostics:
   - `## Diagnostics`
   - `## Last Error Reasons`
6. If sources are blocked, reduce `--min-results` temporarily and increase `--max-rounds`.

## Output guarantees
- Output files are always written (even with zero results).
- Markdown always includes diagnostics and last error reasons.
- JSON always includes:
  - `meta`
  - `diagnostics`
  - `last_error_reasons`
  - `items`

## Cron-ready overnight example
Run daily at 02:10 AM:

```cron
10 2 * * * cd /Users/ryan/.openclaw/workspace && /usr/bin/python3 skills/sg-quant-jobs-brief/sg_quant_jobs_brief.py --output skills/sg-quant-jobs-brief/outputs/brief-$(date +\%F).md --json-output skills/sg-quant-jobs-brief/outputs/brief-$(date +\%F).json --max-pages 3 --max-rounds 4 --min-results 5 --use-browser >> skills/sg-quant-jobs-brief/outputs/cron.log 2>&1
```


## Chat-ready output (new)
Use these options to print Telegram-ready lines directly:
- `--exclude-developer` : remove titles containing developer
- `--top 25` : keep top 25 by recency
- `--chat-format` : print chat-ready bullet list
- `--chat-output <path>` : also write chat-ready text file

Example:
```bash
python3 skills/sg-quant-jobs-brief/sg_quant_jobs_brief.py   --output skills/sg-quant-jobs-brief/outputs/brief-chat.md   --json-output skills/sg-quant-jobs-brief/outputs/brief-chat.json   --max-pages 3 --max-rounds 4 --min-results 5 --use-browser   --exclude-developer --top 25 --chat-format   --chat-output skills/sg-quant-jobs-brief/outputs/brief-chat.txt
```
