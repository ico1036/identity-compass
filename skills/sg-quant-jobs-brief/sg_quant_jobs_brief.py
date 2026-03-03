#!/usr/bin/env python3
"""
sg_quant_jobs_brief.py
Collect and brief Singapore quant jobs (quant researcher / quant trader)
from LinkedIn and Glassdoor only, then apply Ralph-loop quality checks.

v2 notes:
- Fast path: requests/urllib scraping with retries and pagination
- Fallback: Playwright browser collector (optional)
- Round-based retries with --min-results / --max-rounds stop control
- Always emits diagnostics and last error reasons in markdown + JSON outputs
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import random
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ALLOWED_SOURCES = {"linkedin.com": "LinkedIn", "glassdoor.com": "Glassdoor"}
ROLE_PATTERNS = [
    r"\bquant(?:itative)?\s+research(?:er)?\b",
    r"\bquant(?:itative)?\s+trader?\b",
    r"\balgo(?:rithmic)?\s+trader?\b",
    r"\bsystematic\s+trader?\b",
    r"\bquant\s+analyst\b",
    r"\bqr\b",
    r"\bqt\b",
    r"\bquant\b",
]

# Rotated per request/round to reduce static fingerprinting.
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]

REQUEST_TIMEOUT_SEC = 18
REQUEST_RETRIES = 2
BASE_BACKOFF_SEC = 1.0

LINKEDIN_KEYWORDS = [
    "quant researcher",
    "quant trader",
]
GLASSDOOR_KEYWORDS = [
    "quant researcher",
    "quant trader",
]


@dataclass
class JobItem:
    source: str
    title: str
    company: str
    location: str
    date_posted: str
    link: str
    confidence: float = 0.0
    reasons: Optional[List[str]] = None


def pick_user_agent() -> str:
    return random.choice(USER_AGENTS)


def clean_text(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()


def parse_relative_date(raw: str) -> str:
    raw = (raw or "").strip().lower()
    if not raw:
        return ""

    now = dt.datetime.now().date()
    if any(x in raw for x in ["just posted", "today"]):
        return now.isoformat()
    if "yesterday" in raw:
        return (now - dt.timedelta(days=1)).isoformat()

    m = re.search(r"(\d+)\+?\s*(hour|day|week|month|year)", raw)
    if not m:
        # Try ISO-ish date
        try:
            d = dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
            return d.isoformat()
        except Exception:
            return ""

    n = int(m.group(1))
    unit = m.group(2)
    delta_days = {"hour": 0, "day": n, "week": n * 7, "month": n * 30, "year": n * 365}[unit]
    return (now - dt.timedelta(days=delta_days)).isoformat()




def parse_result_count_text(body: str, source_hint: str) -> Optional[int]:
    text = clean_text(body)
    patterns = []
    if source_hint == "LinkedIn":
        patterns = [
            r"([\d,]+)\s+results",
            r"showing\s+[\d,]+\s*[-to]+\s*[\d,]+\s+of\s+([\d,]+)",
        ]
    elif source_hint == "Glassdoor":
        patterns = [
            r"([\d,]+)\s+jobs",
            r"([\d,]+)\s+job\s+results",
        ]
    else:
        patterns = [r"([\d,]+)\s+(?:results|jobs)"]

    for pat in patterns:
        m = re.search(pat, text, flags=re.I)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except Exception:
                continue
    return None


def infer_context_from_url(url: str) -> Tuple[bool, bool]:
    u = (url or "").lower()
    parsed = urllib.parse.urlparse(u)
    bag = " ".join([parsed.path, parsed.query, parsed.fragment])
    role_hit = any(k in bag for k in [
        "quant",
        "quantitative",
        "quant+research",
        "quant+trader",
        "quant%20research",
        "quant%20trader",
        "systematic",
        "algorithmic",
    ])
    sg_hit = any(k in bag for k in ["singapore", "in217", "lockeyword=singapore", "location=singapore"])
    return role_hit, sg_hit


def infer_title_from_anchor_tag(anchor_tag: str, fallback_text: str = "") -> str:
    for pat in [r'aria-label="([^"]+)"', r'title="([^"]+)"', r'data-job-title="([^"]+)"']:
        m = re.search(pat, anchor_tag, flags=re.I)
        if m:
            t = clean_text(m.group(1))
            if t:
                return t
    return clean_text(fallback_text)
def is_allowed_url(url: str) -> bool:
    host = urllib.parse.urlparse(url).netloc.lower()
    return any(domain in host for domain in ALLOWED_SOURCES.keys())


def role_valid(title: str) -> bool:
    t = (title or "").lower()
    return any(re.search(p, t) for p in ROLE_PATTERNS)


def location_valid(location: str) -> bool:
    return "singapore" in (location or "").lower()


def fresh_enough(date_posted: str, max_age_days: int = 60) -> bool:
    try:
        d = dt.date.fromisoformat(date_posted)
        return (dt.date.today() - d).days <= max_age_days
    except Exception:
        return False




def is_developer_title(title: str) -> bool:
    return "developer" in (title or "").lower()


def sort_by_recency(items: List[JobItem]) -> List[JobItem]:
    def k(it: JobItem):
        try:
            return dt.date.fromisoformat(it.date_posted or "1970-01-01")
        except Exception:
            return dt.date(1970,1,1)
    return sorted(items, key=k, reverse=True)


def render_chat_list(items: List[JobItem]) -> str:
    lines=[]
    for i,it in enumerate(items,1):
        lines += [
            f"{i}) {it.title} — {it.company}",
            f"- {it.location} / {it.date_posted}",
            f"- 요약: {it.title} 포지션",
            f"- 특이: {'크립토/디지털자산' if 'crypto' in (it.title or '').lower() else '정량 리서치/트레이딩 직무'}",
            f"- 링크: {it.link}",
            "",
        ]
    return "\n".join(lines).strip()+"\n"

def score_item(item: JobItem) -> float:
    score = 0.0
    if item.title:
        score += 0.2
    if item.company:
        score += 0.2
    if item.link and is_allowed_url(item.link):
        score += 0.2
    if item.date_posted and fresh_enough(item.date_posted):
        score += 0.2
    if role_valid(item.title) and location_valid(item.location):
        score += 0.2
    return round(score, 2)


def fetch_url_with_retry(url: str, logs: List[str], error_reasons: List[str], timeout: int = REQUEST_TIMEOUT_SEC) -> str:
    last_err = ""
    for attempt in range(1, REQUEST_RETRIES + 1):
        ua = pick_user_agent()
        req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Language": "en-SG,en;q=0.9"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                logs.append(f"GET ok [{attempt}/{REQUEST_RETRIES}] {url}")
                return body
        except Exception as e:
            last_err = str(e)
            wait = BASE_BACKOFF_SEC * (2 ** (attempt - 1)) + random.uniform(0.2, 1.0)
            logs.append(f"GET fail [{attempt}/{REQUEST_RETRIES}] {url} :: {e} (sleep {wait:.1f}s)")
            time.sleep(wait)
    error_reasons.append(f"fetch_failed: {url} :: {last_err}")
    return ""


def build_linkedin_urls(keyword: str, max_pages: int) -> List[str]:
    urls: List[str] = []
    for page in range(max_pages):
        start = page * 25
        params_api = {"keywords": keyword, "location": "Singapore", "start": str(start)}
        urls.append(
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
            + urllib.parse.urlencode(params_api)
        )

        params_search = {
            "keywords": keyword,
            "location": "Singapore",
            "trk": "public_jobs_jobs-search-bar_search-submit",
            "position": "1",
            "pageNum": str(page),
            "start": str(start),
        }
        urls.append("https://www.linkedin.com/jobs/search/?" + urllib.parse.urlencode(params_search))
    return urls


def build_glassdoor_urls(keyword: str, max_pages: int) -> List[str]:
    q = urllib.parse.quote_plus(keyword)
    urls: List[str] = []
    for page in range(max_pages):
        # Known public templates; Glassdoor markup often changes, so we try several.
        urls.append(f"https://www.glassdoor.com/Job/singapore-{q}-jobs-SRCH_IL.0,9_IN217_KO10,40_IP{page+1}.htm")
        urls.append(f"https://www.glassdoor.com/Job/singapore-{q}-jobs-SRCH_IL.0,9_IN217.htm?fromAge=7&pgc={page+1}")
        urls.append(f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={q}&locT=C&locId=114&locKeyword=Singapore&p={page+1}")
    return urls


def extract_jobs_from_html(body: str, source_hint: str, page_url: str = "") -> List[JobItem]:
    jobs: List[JobItem] = []

    page_role_hint, page_loc_hint = infer_context_from_url(page_url)

    # Generic anchor extraction with fallback mode for index pages/card schema drift.
    for m in re.finditer(r'(<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>)', body, flags=re.S | re.I):
        raw_anchor = m.group(1)
        href = (m.group(2) or "").strip()
        text = clean_text(m.group(3))
        if not href:
            continue

        full = href
        if href.startswith("/"):
            if source_hint == "LinkedIn":
                full = "https://www.linkedin.com" + href
            elif source_hint == "Glassdoor":
                full = "https://www.glassdoor.com" + href

        if not is_allowed_url(full):
            continue

        low = full.lower()
        looks_listing = False
        if "linkedin.com" in low:
            looks_listing = ("/jobs/view" in low) or ("currentjobid=" in low) or ("jobs-guest/jobs/api" in low)
        if "glassdoor.com" in low:
            looks_listing = looks_listing or ("joblistingid=" in low) or ("/job-listing/" in low) or ("/partner/joblisting.htm" in low)
        if not looks_listing:
            continue

        title = infer_title_from_anchor_tag(raw_anchor, text)

        idx = m.start()
        card = body[max(0, idx - 700): idx + 2200]
        company = ""
        location = ""
        date_posted = ""

        company_matchers = [
            r'base-search-card__subtitle[^>]*>(.*?)</',
            r'employerName[^>]*>(.*?)</',
            r'data-test="employer-name"[^>]*>(.*?)</',
            r'topcard__org-name-link[^>]*>(.*?)</',
        ]
        for cm in company_matchers:
            cm_m = re.search(cm, card, flags=re.S | re.I)
            if cm_m:
                company = clean_text(cm_m.group(1))
                break

        loc_matchers = [
            r'job-search-card__location[^>]*>(.*?)</',
            r'locationName[^>]*>(.*?)</',
            r'data-test="emp-location"[^>]*>(.*?)</',
            r'jobLocation[^>]*>(.*?)</',
        ]
        for lm in loc_matchers:
            lm_m = re.search(lm, card, flags=re.S | re.I)
            if lm_m:
                location = clean_text(lm_m.group(1))
                break

        date_match = re.search(r'<time[^>]*datetime="([^"]+)"', card, flags=re.I)
        if date_match:
            date_posted = parse_relative_date(date_match.group(1))
        else:
            rel_match = re.search(r'(\d+\+?\s*(?:hour|day|week|month|year)s?\s+ago|today|yesterday|just posted)', card, flags=re.I)
            if rel_match:
                date_posted = parse_relative_date(rel_match.group(1))

        role_hit = role_valid(title)
        loc_hit = location_valid(location)
        role_hint, loc_hint = infer_context_from_url(full)

        reasons: List[str] = []
        if not role_hit and (role_hint or page_role_hint):
            reasons.append("role_inferred_from_url_query")
            role_hit = True
        if not loc_hit and (loc_hint or page_loc_hint):
            location = location or "Singapore (inferred)"
            reasons.append("location_inferred_from_url_query")
            loc_hit = True

        if not (role_hit and loc_hit):
            continue

        if reasons:
            reasons.append("lower_confidence_fallback")

        source = "LinkedIn" if "linkedin.com" in low else "Glassdoor"
        jobs.append(JobItem(source=source, title=title or "(untitled)", company=company, location=location or "Singapore", date_posted=date_posted, link=full, reasons=reasons))

    return jobs


def fetch_requests_path(max_pages: int, logs: List[str], error_reasons: List[str]) -> List[JobItem]:
    jobs: List[JobItem] = []

    for kw in LINKEDIN_KEYWORDS:
        for url in build_linkedin_urls(kw, max_pages=max_pages):
            body = fetch_url_with_retry(url, logs, error_reasons)
            if not body:
                continue
            extracted = extract_jobs_from_html(body, "LinkedIn", page_url=url)
            rc = parse_result_count_text(body, "LinkedIn")
            logs.append(f"LinkedIn extracted {len(extracted)} from template URL; index_count={rc if rc is not None else 'n/a'}")
            jobs.extend(extracted)
            time.sleep(random.uniform(0.8, 1.7))

    for kw in GLASSDOOR_KEYWORDS:
        for url in build_glassdoor_urls(kw, max_pages=max_pages):
            body = fetch_url_with_retry(url, logs, error_reasons)
            if not body:
                continue
            extracted = extract_jobs_from_html(body, "Glassdoor", page_url=url)
            rc = parse_result_count_text(body, "Glassdoor")
            logs.append(f"Glassdoor extracted {len(extracted)} from template URL; index_count={rc if rc is not None else 'n/a'}")
            jobs.extend(extracted)
            time.sleep(random.uniform(0.8, 1.7))

    return jobs


def fetch_browser_path(max_pages: int, headful: bool, logs: List[str], error_reasons: List[str]) -> List[JobItem]:
    jobs: List[JobItem] = []
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        error_reasons.append(f"browser_unavailable: {e}")
        logs.append("Playwright import failed; browser collector skipped.")
        return jobs

    all_urls: List[Tuple[str, str]] = []
    for kw in LINKEDIN_KEYWORDS:
        all_urls.extend([("LinkedIn", u) for u in build_linkedin_urls(kw, max_pages=max_pages)])
    for kw in GLASSDOOR_KEYWORDS:
        all_urls.extend([("Glassdoor", u) for u in build_glassdoor_urls(kw, max_pages=max_pages)])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headful, slow_mo=120 if headful else 0)
        context = browser.new_context(user_agent=pick_user_agent(), locale="en-SG", timezone_id="Asia/Singapore")
        page = context.new_page()
        page.set_default_navigation_timeout(90000)
        page.set_default_timeout(90000)

        for source, url in all_urls:
            try:
                logs.append(f"Browser nav: {url}")
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(int(random.uniform(1200, 3000)))
                try:
                    page.mouse.wheel(0, random.randint(1200, 3000))
                    page.wait_for_timeout(int(random.uniform(800, 1800)))
                except Exception:
                    pass
                body = page.content()
                extracted = extract_jobs_from_html(body, source, page_url=url)
                rc = parse_result_count_text(body, source)
                logs.append(f"Browser {source} extracted {len(extracted)} from {url}; index_count={rc if rc is not None else 'n/a'}")
                jobs.extend(extracted)
            except Exception as e:
                msg = f"browser_nav_failed: {url} :: {e}"
                logs.append(msg)
                error_reasons.append(msg)

        context.close()
        browser.close()

    return jobs


def ralph_loop(items: List[JobItem], max_iter: int = 5) -> Tuple[List[JobItem], List[str], List[str]]:
    logs: List[str] = []
    current = items[:]
    rejected_reasons: List[str] = []

    for i in range(1, max_iter + 1):
        before = len(current)
        checked: List[JobItem] = []

        for it in current:
            it.reasons = (it.reasons or []).copy()
            hard_reasons: List[str] = []
            if not is_allowed_url(it.link):
                hard_reasons.append("source_not_whitelisted")
            if not location_valid(it.location):
                hard_reasons.append("invalid_location")
            if not role_valid(it.title) and "role_inferred_from_url_query" not in it.reasons:
                hard_reasons.append("invalid_role")
            if it.date_posted and not fresh_enough(it.date_posted):
                hard_reasons.append("stale_date")

            if not it.company:
                it.reasons.append("missing_company_soft")
            if not it.date_posted:
                it.reasons.append("missing_date_soft")

            it.confidence = score_item(it)
            if "lower_confidence_fallback" in it.reasons:
                it.confidence = max(0.35, round(it.confidence - 0.15, 2))

            if not hard_reasons:
                checked.append(it)
            else:
                it.reasons.extend(hard_reasons)
                rejected_reasons.append(f"{it.source}|{it.title[:80]} :: {','.join(it.reasons)}")

        deduped: Dict[str, JobItem] = {}
        for it in checked:
            key = f"{it.source}|{it.company.strip().lower()}|{it.title.strip().lower()}|{it.link.strip().lower()}"
            if key not in deduped:
                deduped[key] = it

        current = list(deduped.values())
        after = len(current)
        removed = before - after
        logs.append(f"Ralph-loop iter {i}: {before} -> {after} (removed {removed})")
        if removed == 0:
            logs.append(f"Ralph-loop converged at iter {i}.")
            break

    return current, logs, rejected_reasons


def render_markdown(items: List[JobItem], logs: List[str], errors: List[str], min_results: int, rounds_done: int) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    lines = [
        "# Singapore Quant Jobs Brief",
        "",
        f"Generated: {now}",
        "",
        "## Scope",
        "- Sources: LinkedIn, Glassdoor only",
        "- Roles: Quant Researcher / Quant Trader (+ close variants)",
        "- Location: Singapore only",
        f"- Min target results: {min_results}",
        f"- Rounds executed: {rounds_done}",
        "",
        "## Diagnostics",
    ]
    lines.extend([f"- {l}" for l in logs] or ["- No diagnostics logs."])
    lines.append("")
    lines.append("## Last Error Reasons")
    if errors:
        # Show latest distinct reasons only.
        seen = set()
        for e in reversed(errors):
            if e in seen:
                continue
            seen.add(e)
            lines.append(f"- {e}")
            if len(seen) >= 12:
                break
    else:
        lines.append("- None")

    lines.append("")
    lines.append(f"## Final Shortlist ({len(items)} roles)")
    lines.append("")
    if not items:
        lines.append("No qualifying jobs found in accessible pages during this run.")
    for i, it in enumerate(items, 1):
        lines.extend([
            f"### {i}. {it.title} — {it.company}",
            f"- Source: {it.source}",
            f"- Location: {it.location}",
            f"- Date: {it.date_posted}",
            f"- Confidence: {it.confidence}",
            f"- Link: {it.link}",
            "",
        ])
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="outputs/sg-quant-jobs-brief.md")
    ap.add_argument("--json-output", default="outputs/sg-quant-jobs-brief.json")
    ap.add_argument("--max-pages", type=int, default=2)
    ap.add_argument("--use-browser", action="store_true", help="Enable Playwright fallback collector")
    ap.add_argument("--headful", action="store_true", help="Run browser visibly (effective with --use-browser)")
    ap.add_argument("--min-results", type=int, default=0, help="Require at least this many final results before early stop")
    ap.add_argument("--max-rounds", type=int, default=3, help="Max retry rounds for collection + QA")
    ap.add_argument("--exclude-developer", action="store_true", help="Exclude titles containing developer")
    ap.add_argument("--top", type=int, default=0, help="Return top N by recency after filtering (0=all)")
    ap.add_argument("--chat-format", action="store_true", help="Emit chat-ready list format")
    ap.add_argument("--chat-output", default="", help="Optional path to write chat-ready output")
    args = ap.parse_args()

    output_path = Path(args.output)
    json_path = Path(args.json_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    all_logs: List[str] = []
    all_errors: List[str] = []
    final_items: List[JobItem] = []
    rounds_done = 0

    for rnd in range(1, max(1, args.max_rounds) + 1):
        rounds_done = rnd
        round_logs: List[str] = [f"=== Round {rnd}/{args.max_rounds} ==="]
        round_errors: List[str] = []

        collected = fetch_requests_path(max_pages=max(0, args.max_pages), logs=round_logs, error_reasons=round_errors)

        # Fallback automatically when requested and requests path underperforms.
        if args.use_browser and len(collected) < max(5, args.min_results):
            round_logs.append("Invoking browser fallback collector due to low fast-path yield.")
            collected.extend(fetch_browser_path(max_pages=max(0, args.max_pages), headful=args.headful, logs=round_logs, error_reasons=round_errors))

        filtered, qa_logs, rejected = ralph_loop(collected)
        round_logs.extend(qa_logs)
        if rejected:
            round_errors.extend(rejected[-30:])

        all_logs.extend(round_logs)
        all_errors.extend(round_errors)
        final_items = filtered

        all_logs.append(f"Round {rnd} final count: {len(final_items)}")
        if len(final_items) >= max(0, args.min_results):
            all_logs.append(f"Stop condition met: {len(final_items)} >= min-results {args.min_results}")
            break
        if rnd < max(1, args.max_rounds):
            all_logs.append("Stop condition not met; continuing to next round.")
        else:
            all_logs.append("Stop condition not met; max rounds reached.")

    final_items = sort_by_recency(final_items)
    if args.exclude_developer:
        final_items = [i for i in final_items if not is_developer_title(i.title)]
    if args.top and args.top > 0:
        final_items = final_items[:args.top]

    md = render_markdown(final_items, all_logs, all_errors, min_results=max(0, args.min_results), rounds_done=rounds_done)
    output_path.write_text(md, encoding="utf-8")

    payload = {
        "meta": {
            "generated_at": dt.datetime.now().isoformat(),
            "min_results": max(0, args.min_results),
            "max_rounds": max(1, args.max_rounds),
            "rounds_done": rounds_done,
            "final_count": len(final_items),
        },
        "diagnostics": all_logs,
        "last_error_reasons": all_errors[-50:],
        "items": [asdict(j) for j in final_items],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote markdown: {output_path}")
    print(f"Wrote json: {json_path}")
    if args.chat_format:
        chat = render_chat_list(final_items)
        if args.chat_output:
            Path(args.chat_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.chat_output).write_text(chat, encoding="utf-8")
            print(f"Wrote chat output: {args.chat_output}")
        print("---CHAT_FORMAT_START---")
        print(chat)
        print("---CHAT_FORMAT_END---")

    print(f"Final result count: {len(final_items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
