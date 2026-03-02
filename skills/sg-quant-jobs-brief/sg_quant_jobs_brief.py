#!/usr/bin/env python3
"""
sg_quant_jobs_brief.py
Collect and brief Singapore quant jobs (quant researcher / quant trader)
from LinkedIn and Glassdoor only, then apply Ralph-loop quality checks.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Tuple

USER_AGENT = "Mozilla/5.0 (compatible; sg-quant-jobs-brief/1.0; +https://openclaw.local)"
ALLOWED_SOURCES = {"linkedin.com": "LinkedIn", "glassdoor.com": "Glassdoor"}
ROLE_PATTERNS = [
    r"\bquant(?:itative)?\s+research(?:er)?\b",
    r"\bquant(?:itative)?\s+trader?\b",
    r"\balgo(?:rithmic)?\s+trader?\b",
    r"\bsystematic\s+trader?\b",
    r"\bquant\s+analyst\b",
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
    reasons: List[str] = None


def fetch_url(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def can_fetch(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return False


def clean_text(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()


def parse_relative_date(raw: str) -> str:
    raw = (raw or "").strip().lower()
    if not raw:
        return ""
    now = dt.datetime.now().date()
    m = re.search(r"(\d+)\+?\s*(day|hour|week|month|year)", raw)
    if not m:
        try:
            d = dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
            return d.isoformat()
        except Exception:
            return ""
    n = int(m.group(1))
    unit = m.group(2)
    delta_days = 0
    if unit == "hour":
        delta_days = 0
    elif unit == "day":
        delta_days = n
    elif unit == "week":
        delta_days = n * 7
    elif unit == "month":
        delta_days = n * 30
    elif unit == "year":
        delta_days = n * 365
    return (now - dt.timedelta(days=delta_days)).isoformat()


def fetch_linkedin_jobs(max_pages: int = 2) -> Tuple[List[JobItem], List[str]]:
    logs: List[str] = []
    jobs: List[JobItem] = []
    base = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    for kw in ["quant researcher", "quant trader"]:
        for page in range(max_pages):
            start = page * 25
            params = {
                "keywords": kw,
                "location": "Singapore",
                "start": str(start),
            }
            url = f"{base}?{urllib.parse.urlencode(params)}"
            if not can_fetch(url):
                logs.append(f"LinkedIn blocked by robots for {kw} page {page}.")
                break
            try:
                body = fetch_url(url)
            except Exception as e:
                logs.append(f"LinkedIn fetch failed ({kw}, page {page}): {e}")
                break

            cards = re.findall(r"(<li>.*?</li>)", body, flags=re.S)
            if not cards:
                logs.append(f"LinkedIn returned no cards ({kw}, page {page}).")
                break

            for card in cards:
                href_m = re.search(r'href="([^"]+)"', card)
                title_m = re.search(r"job-search-card__title[^>]*>(.*?)</", card, flags=re.S)
                comp_m = re.search(r"base-search-card__subtitle[^>]*>(.*?)</", card, flags=re.S)
                loc_m = re.search(r"job-search-card__location[^>]*>(.*?)</", card, flags=re.S)
                time_m = re.search(r"<time[^>]*datetime=\"([^\"]+)\"", card)
                time_text_m = re.search(r"<time[^>]*>(.*?)</time>", card, flags=re.S)

                link = (href_m.group(1).strip() if href_m else "")
                title = clean_text(title_m.group(1) if title_m else "")
                company = clean_text(comp_m.group(1) if comp_m else "")
                location = clean_text(loc_m.group(1) if loc_m else "")
                date_raw = time_m.group(1) if time_m else (clean_text(time_text_m.group(1)) if time_text_m else "")
                date_posted = parse_relative_date(date_raw)

                jobs.append(JobItem(
                    source="LinkedIn",
                    title=title,
                    company=company,
                    location=location,
                    date_posted=date_posted,
                    link=link,
                    reasons=[],
                ))
            time.sleep(0.4)
    return jobs, logs


def fetch_glassdoor_jobs(max_pages: int = 1) -> Tuple[List[JobItem], List[str]]:
    logs: List[str] = []
    jobs: List[JobItem] = []
    for kw in ["quant researcher", "quant trader"]:
        query = urllib.parse.quote_plus(kw)
        url = f"https://www.glassdoor.com/Job/singapore-{query}-jobs-SRCH_IL.0,9_IN217_KO10,26.htm"
        if not can_fetch(url):
            logs.append(f"Glassdoor blocked by robots for {kw}.")
            continue
        try:
            body = fetch_url(url)
        except Exception as e:
            logs.append(f"Glassdoor fetch failed ({kw}): {e}")
            continue

        cards = re.findall(r"(href=\"/job-listing/.*?</article>)", body, flags=re.S)
        if not cards:
            logs.append(f"Glassdoor returned no parseable cards ({kw}).")
            continue

        for c in cards[: max_pages * 20]:
            href_m = re.search(r'href="([^"]+/job-listing/[^"]+)"', c)
            title_m = re.search(r"jobTitle[^>]*>(.*?)</", c, flags=re.S)
            comp_m = re.search(r"employerName[^>]*>(.*?)</", c, flags=re.S)
            loc_m = re.search(r"locationName[^>]*>(.*?)</", c, flags=re.S)
            date_m = re.search(r"job-age[^>]*>(.*?)</", c, flags=re.S)

            link = "https://www.glassdoor.com" + href_m.group(1) if href_m else ""
            title = clean_text(title_m.group(1) if title_m else "")
            company = clean_text(comp_m.group(1) if comp_m else "")
            location = clean_text(loc_m.group(1) if loc_m else "")
            date_posted = parse_relative_date(clean_text(date_m.group(1) if date_m else ""))

            jobs.append(JobItem(
                source="Glassdoor",
                title=title,
                company=company,
                location=location,
                date_posted=date_posted,
                link=link,
                reasons=[],
            ))
    return jobs, logs


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


def ralph_loop(items: List[JobItem], max_iter: int = 5) -> Tuple[List[JobItem], List[str]]:
    logs = []
    current = items[:]

    for i in range(1, max_iter + 1):
        before = len(current)
        checked: List[JobItem] = []

        # remove invalid required/source/location/role/freshness
        for it in current:
            it.reasons = []
            required = all([it.company, it.title, it.link, it.date_posted, it.source])
            if not required:
                it.reasons.append("missing_required_fields")
            if not is_allowed_url(it.link):
                it.reasons.append("source_not_whitelisted")
            if not location_valid(it.location):
                it.reasons.append("invalid_location")
            if not role_valid(it.title):
                it.reasons.append("invalid_role")
            if not fresh_enough(it.date_posted):
                it.reasons.append("stale_or_unknown_date")

            it.confidence = score_item(it)
            if not it.reasons:
                checked.append(it)

        # dedupe
        deduped: Dict[str, JobItem] = {}
        for it in checked:
            key = f"{it.source}|{it.company.strip().lower()}|{it.title.strip().lower()}"
            if key not in deduped:
                deduped[key] = it

        current = list(deduped.values())
        after = len(current)
        removed = before - after
        logs.append(f"Ralph-loop iter {i}: {before} -> {after} (removed {removed})")

        if removed == 0:
            logs.append(f"Ralph-loop converged at iter {i}.")
            break

    return current, logs


def render_markdown(items: List[JobItem], logs: List[str]) -> str:
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
        "",
        "## Ralph-loop QA Log",
    ]
    lines.extend([f"- {l}" for l in logs] or ["- No QA logs."])
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
    args = ap.parse_args()

    all_logs: List[str] = []
    linkedin_jobs, linkedin_logs = fetch_linkedin_jobs()
    glassdoor_jobs, glassdoor_logs = fetch_glassdoor_jobs()
    all_logs.extend(linkedin_logs)
    all_logs.extend(glassdoor_logs)

    combined = linkedin_jobs + glassdoor_jobs
    filtered, qa_logs = ralph_loop(combined)
    all_logs.extend(qa_logs)

    output_path = Path(args.output)
    json_path = Path(args.json_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(render_markdown(filtered, all_logs), encoding="utf-8")
    json_path.write_text(json.dumps([asdict(j) for j in filtered], ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote markdown: {output_path}")
    print(f"Wrote json: {json_path}")
    print(f"Final result count: {len(filtered)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
