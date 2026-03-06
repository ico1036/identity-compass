#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

STOP = {"the","and","for","with","from","that","this","are","you","your","our","role","team","will","using","use"}


def read_text(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8")


def tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9+.#-]{2,}", text.lower())


def top_keywords(text: str, n: int = 20) -> list[tuple[str,int]]:
    c = Counter(t for t in tokens(text) if t not in STOP)
    return c.most_common(n)


def detect_themes(text: str) -> dict:
    low = text.lower()
    themes = {
        "research": int(any(k in low for k in ["research", "signal", "hypothesis", "alpha"])),
        "trading": int(any(k in low for k in ["trading", "execution", "portfolio"])),
        "risk": int(any(k in low for k in ["risk", "robust", "validation"])),
        "ml": int(any(k in low for k in ["machine learning", "xgboost", "pytorch", "model"])),
        "engineering": int(any(k in low for k in ["production", "pipeline", "infrastructure", "latency"])),
    }
    return themes


def resume_gaps(resume_text: str, kw: list[tuple[str,int]]) -> list[str]:
    rt = set(tokens(resume_text))
    missing = [k for k,_ in kw if k not in rt]
    return missing[:10]


def main() -> None:
    ap = argparse.ArgumentParser(description="Company-fit research layer for resume tailoring")
    ap.add_argument("--company", required=True)
    ap.add_argument("--jds-file", required=True)
    ap.add_argument("--resume-file", required=True)
    ap.add_argument("--notes-file")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    jds = read_text(args.jds_file)
    resume = read_text(args.resume_file)
    notes = read_text(args.notes_file)
    combined = "\n".join([jds, notes]).strip()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    kw = top_keywords(combined, 24)
    themes = detect_themes(combined)
    gaps = resume_gaps(resume, kw)

    fit = {
        "company": args.company,
        "top_keywords": kw,
        "themes": themes,
        "resume_gaps": gaps,
    }
    (out / "fit_signals.json").write_text(json.dumps(fit, indent=2, ensure_ascii=False), encoding="utf-8")

    brief = [
        f"# {args.company} Company Fit Brief",
        "",
        "## Hiring signals (from recent JD text)",
        "- Top keywords: " + ", ".join(k for k,_ in kw[:12]),
        f"- Dominant themes: " + ", ".join(k for k,v in themes.items() if v) if any(themes.values()) else "- Dominant themes: unclear",
        "",
        "## Implication",
        "- Prioritize bullets matching these themes in summary and top 3 experience bullets.",
        "- Keep role language specific to company/team context.",
    ]
    (out / "company_fit_brief.md").write_text("\n".join(brief) + "\n", encoding="utf-8")

    delta = [
        f"# Resume Delta for {args.company}",
        "",
        "## Add / strengthen",
    ]
    if gaps:
        delta += [f"- Add evidence-backed mention for: {', '.join(gaps[:8])}"]
    else:
        delta += ["- No major keyword gaps detected."]
    delta += [
        "",
        "## Tone",
        "- Align summary opening to company’s dominant theme (research/risk/engineering/trading).",
        "- Keep claims grounded; no ownership inflation.",
        "",
        "## Next step",
        "- Apply edits to markdown resume, then run resume-ralph-loop.",
    ]
    (out / "resume_delta.md").write_text("\n".join(delta) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
