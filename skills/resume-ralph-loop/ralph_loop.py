#!/usr/bin/env python3
"""resume-ralph-loop skeleton

Accepts resume text + JD text and prints a JSON diagnostics report.
Current gates:
- keyword coverage
- quantified achievements present
- genericness heuristic
- consistency flags
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Dict


STOPWORDS = {
    "the", "and", "or", "to", "of", "in", "for", "with", "on", "a", "an", "is",
    "are", "as", "by", "from", "at", "be", "this", "that", "will", "you", "your",
}

GENERIC_PHRASES = [
    "team player",
    "hard worker",
    "fast learner",
    "detail-oriented",
    "results-driven",
    "self-starter",
]


@dataclass
class KeywordCoverage:
    extracted_keywords: List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]
    coverage_ratio: float


@dataclass
class QuantifiedAchievementsGate:
    passed: bool
    count: int
    examples: List[str]


@dataclass
class GenericnessHeuristic:
    generic_phrase_hits: int
    generic_phrases_found: List[str]
    score: float  # higher = more generic


@dataclass
class Report:
    keyword_coverage: Dict
    quantified_achievements_present: Dict
    genericness_heuristic: Dict
    consistency_flags: Dict


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9+.#-]{1,}", text.lower())


def extract_jd_keywords(jd_text: str, top_n: int = 25) -> List[str]:
    freq: Dict[str, int] = {}
    for tok in tokenize(jd_text):
        if tok in STOPWORDS or len(tok) < 3:
            continue
        freq[tok] = freq.get(tok, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)
    return [k for k, _ in ranked[:top_n]]


def keyword_coverage(resume_text: str, jd_text: str) -> KeywordCoverage:
    jd_keywords = extract_jd_keywords(jd_text)
    resume_tokens = set(tokenize(resume_text))
    matched = [k for k in jd_keywords if k in resume_tokens]
    missing = [k for k in jd_keywords if k not in resume_tokens]
    ratio = (len(matched) / len(jd_keywords)) if jd_keywords else 0.0
    return KeywordCoverage(jd_keywords, matched, missing, round(ratio, 3))


def quantified_achievements_gate(resume_text: str) -> QuantifiedAchievementsGate:
    lines = [ln.strip() for ln in resume_text.splitlines() if ln.strip()]
    metric_pattern = re.compile(r"(\d+\s?%|\$\s?\d+|\d+x|\d+\+?|\d{4})")
    hits = [ln for ln in lines if metric_pattern.search(ln)]
    return QuantifiedAchievementsGate(
        passed=len(hits) > 0,
        count=len(hits),
        examples=hits[:5],
    )


def genericness_heuristic(resume_text: str) -> GenericnessHeuristic:
    low = resume_text.lower()
    found = [p for p in GENERIC_PHRASES if p in low]
    # Simple score: phrase density against document length.
    denom = max(len(low.split()), 1)
    score = round((len(found) * 100) / denom, 3)
    return GenericnessHeuristic(
        generic_phrase_hits=len(found),
        generic_phrases_found=found,
        score=score,
    )


def consistency_flags(resume_text: str) -> Dict:
    flags = []

    years = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", resume_text)]
    if years:
        if min(years) < 1970:
            flags.append("suspicious_old_year_detected")
        if max(years) > 2100:
            flags.append("future_year_detected")

    if "present" in resume_text.lower() and re.search(r"\b(ended|finished)\b", resume_text.lower()):
        flags.append("potential_tense_timeline_conflict")

    return {
        "passed": len(flags) == 0,
        "flags": flags,
    }


def load_text(direct_text: str | None, file_path: str | None) -> str:
    if direct_text:
        return direct_text
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run resume Ralph-loop skeleton gates.")
    p.add_argument("--resume-text", help="Raw resume text", default=None)
    p.add_argument("--resume-file", help="Path to resume text file", default=None)
    p.add_argument("--jd-text", help="Raw JD text", default=None)
    p.add_argument("--jd-file", help="Path to JD text file", default=None)
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    resume_text = load_text(args.resume_text, args.resume_file)
    jd_text = load_text(args.jd_text, args.jd_file)

    if not resume_text.strip() or not jd_text.strip():
        raise SystemExit("Both resume and JD text are required via --*-text or --*-file.")

    report = Report(
        keyword_coverage=asdict(keyword_coverage(resume_text, jd_text)),
        quantified_achievements_present=asdict(quantified_achievements_gate(resume_text)),
        genericness_heuristic=asdict(genericness_heuristic(resume_text)),
        consistency_flags=consistency_flags(resume_text),
    )

    if args.pretty:
        print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(asdict(report), ensure_ascii=False))


if __name__ == "__main__":
    main()
