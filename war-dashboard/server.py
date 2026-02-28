#!/usr/bin/env python3
import json
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"

USER_AGENT = "Mozilla/5.0 (compatible; OpenClaw-WarDashboard/1.0)"

FEEDS = [
    {
        "name": "Google News (US-Iran query)",
        "url": "https://news.google.com/rss/search?q=" + quote_plus("US Iran conflict OR US Iran war OR Iran retaliation") + "&hl=en-US&gl=US&ceid=US:en",
        "trust": 0.70,
        "kind": "search",
    },
    {
        "name": "Reuters World",
        "url": "https://feeds.reuters.com/Reuters/worldNews",
        "trust": 0.95,
        "kind": "wire",
    },
    {
        "name": "AP Top News",
        "url": "https://feeds.apnews.com/rss/apf-topnews",
        "trust": 0.95,
        "kind": "wire",
    },
    {
        "name": "BBC Middle East",
        "url": "http://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
        "trust": 0.9,
        "kind": "publisher",
    },
    {
        "name": "Al Jazeera Middle East",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "trust": 0.78,
        "kind": "publisher",
    },
]

KEYWORDS = [
    "iran", "tehran", "israel", "u.s.", "us", "american", "middle east",
    "missile", "retaliat", "strike", "drone", "airstrike", "military", "gulf",
]


def score_relevance(title: str, summary: str) -> float:
    text = f"{title} {summary}".lower()
    score = 0
    for kw in KEYWORDS:
        if kw in text:
            score += 1
    if "iran" in text and ("u.s" in text or "us " in text or "american" in text):
        score += 2
    return min(score / 8.0, 1.0)


def parse_date(value: str):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def clean_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


def fetch_rss(feed):
    req = Request(feed["url"], headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=12) as resp:
        data = resp.read()

    root = ET.fromstring(data)
    items = []

    for item in root.findall(".//item")[:30]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = clean_html(item.findtext("description") or "")
        pub = item.findtext("pubDate") or item.findtext("{http://purl.org/dc/elements/1.1/}date")
        dt = parse_date(pub)

        rel = score_relevance(title, desc)
        if rel < 0.2:
            continue

        items.append({
            "title": title,
            "url": link,
            "summary": desc[:240],
            "source": feed["name"],
            "kind": feed["kind"],
            "publishedAt": dt.isoformat() if dt else None,
            "trust": round(feed["trust"], 2),
            "relevance": round(rel, 2),
            "score": round(feed["trust"] * 0.65 + rel * 0.35, 3),
        })

    return items


def aggregate():
    all_items = []
    errors = []

    for feed in FEEDS:
        try:
            all_items.extend(fetch_rss(feed))
        except Exception as e:
            errors.append({"source": feed["name"], "error": str(e)})

    dedup = {}
    for it in all_items:
        key = (it["title"].lower(), urlparse(it["url"]).netloc)
        if key not in dedup or dedup[key]["score"] < it["score"]:
            dedup[key] = it

    rows = sorted(
        dedup.values(),
        key=lambda x: ((x["publishedAt"] or ""), x["score"]),
        reverse=True,
    )

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
        "rows": rows[:80],
        "errors": errors,
        "sources": [{"name": f["name"], "trust": f["trust"], "url": f["url"]} for f in FEEDS],
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, content, ctype="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            self._send(200, INDEX_FILE.read_bytes())
            return

        if self.path.startswith("/api/feed"):
            payload = aggregate()
            self._send(200, json.dumps(payload).encode("utf-8"), "application/json; charset=utf-8")
            return

        self._send(404, b"Not found", "text/plain; charset=utf-8")


if __name__ == "__main__":
    host, port = "127.0.0.1", 8787
    print(f"[war-dashboard] http://{host}:{port}")
    HTTPServer((host, port), Handler).serve_forever()
