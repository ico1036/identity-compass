#!/usr/bin/env python3
"""한국마사회 경주성적표 스크래퍼 — race.kra.co.kr → CSV"""

import requests
import re
import csv
import time
import sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

BASE = "https://race.kra.co.kr"
LIST_URL = f"{BASE}/raceScore/ScoretableScoreList.do"
DETAIL_URL = f"{BASE}/raceScore/ScoretableDetailList.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# meet: 1=서울, 2=제주, 3=부경
MEETS = {"1": "서울", "2": "제주", "3": "부경"}

CSV_COLUMNS = [
    "경마장", "경주일자", "경주번호", "날씨", "주로상태", "함수율", "발주시각",
    "등급", "거리", "별정", "레이팅조건", "연령성별조건",
    # per-horse
    "착순", "출주번호", "마명", "마번_link", "산지", "성별", "연령", "부담중량",
    "레이팅", "기수명", "기수번호", "조교사명", "조교사번호", "마주명", "마주번호",
    "도착차", "마체중", "마체중증감", "단승배당", "연승배당", "장구현황",
    # 구간기록
    "S1F통과순위", "1C통과순위", "2C통과순위", "3C통과순위", "G3F통과순위", "4C통과순위", "G1F통과순위",
    "S1F기록", "1C기록", "2C기록", "3C기록", "G3F기록", "4C기록", "G1F기록",
    "3F_G기록", "1F_G기록", "경주기록",
]


def fetch(url, params=None):
    """Fetch with EUC-KR decoding."""
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    r.encoding = "euc-kr"
    return r.text


def get_race_dates(meet, year, month):
    """Get list of (date_str, [race_nos]) for a given meet/year/month."""
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    from_date = f"{year}{month:02d}01"
    to_date = f"{year}{month:02d}{last_day:02d}"
    
    data = {
        "Act": "04", "Sub": "1", "meet": meet,
        "fromDate": from_date, "toDate": to_date, "pageIndex": "1"
    }
    r = requests.post(LIST_URL, data=data, headers=HEADERS, timeout=30)
    r.encoding = "euc-kr"
    html = r.text
    
    # Also check subsequent pages
    all_html = html
    # Check if there are more pages (up to 5)
    for page in range(2, 6):
        if f"ScoreDetailPopup" not in html:
            break
        data["pageIndex"] = str(page)
        r = requests.post(LIST_URL, data=data, headers=HEADERS, timeout=30)
        r.encoding = "euc-kr"
        page_html = r.text
        if "ScoreDetailPopup" not in page_html:
            break
        all_html += page_html
    
    # Parse ScoreDetailPopup('meet','date','raceNo') calls
    date_races = {}
    for m in re.finditer(r"ScoreDetailPopup\('(\d+)','(\d{8})','(\d+)'\)", all_html):
        mt, d, n = m.group(1), m.group(2), int(m.group(3))
        if mt == meet:
            date_races.setdefault(d, []).append(n)
    
    results = []
    for d in sorted(date_races):
        results.append((d, sorted(set(date_races[d]))))
    return results


def parse_detail(html, meet, rc_date, rc_no):
    """Parse a single race detail page → list of row dicts."""
    soup = BeautifulSoup(html, "html.parser")
    rows_out = []
    
    # Race-level info from first table
    tds = soup.find_all("td")
    td_texts = [td.get_text(strip=True) for td in tds]
    
    # Extract race conditions
    weather = grade = distance = bj = rating_cond = age_sex = ""
    start_time = moisture = track_cond = ""
    
    # Find the condition cells - they follow a known pattern
    for i, t in enumerate(td_texts):
        if "등급" in t:
            grade = t
        if re.match(r"\d+M$", t):
            distance = t
        if t in ("맑음", "흐림", "비", "눈"):
            weather = t
        if t in ("건조", "습윤", "다습", "포화", "불량"):
            track_cond = t
        if re.match(r"\d+%$", t):
            moisture = t
        if re.match(r"\d{1,2}:\d{2}$", t):
            start_time = t
        if "별정" in t or t in ("정량", "핸디캡"):
            bj = t
        if re.match(r"R\d", t):
            rating_cond = t
        if "오픈" in t or "암" in t:
            age_sex = t
    
    race_info = {
        "경마장": MEETS.get(meet, meet),
        "경주일자": rc_date,
        "경주번호": rc_no,
        "날씨": weather,
        "주로상태": track_cond,
        "함수율": moisture,
        "발주시각": start_time,
        "등급": grade,
        "거리": distance,
        "별정": bj,
        "레이팅조건": rating_cond,
        "연령성별조건": age_sex,
    }
    
    # Find score tables
    tables = soup.find_all("table")
    
    # Table with 순위/마번/마명... (성적표)
    score_table = None
    section_table = None
    
    for table in tables:
        ths = [th.get_text(strip=True) for th in table.find_all("th")]
        th_text = " ".join(ths)
        if "마명" in ths and "단승" in ths:
            score_table = table
        if "구간별" in th_text or "펄롱타임" in th_text and "S1F" in th_text:
            section_table = table
        if "통과" in th_text and "누적기록" in th_text:
            section_table = table
    
    if not score_table:
        return rows_out
    
    # Parse score table rows
    horses = []
    tbody = score_table.find("tbody")
    if not tbody:
        tbody = score_table
    
    trs = tbody.find_all("tr")
    for tr in trs:
        cells = tr.find_all("td")
        if len(cells) < 10:
            continue
        
        cell_texts = []
        cell_links = []
        for c in cells:
            cell_texts.append(c.get_text(strip=True))
            # Extract link IDs (horse/jockey/trainer/owner numbers)
            a = c.find("a")
            link_id = ""
            if a:
                onclick = a.get("onclick", "") or a.get("href", "")
                m = re.search(r"'(\d+)'", onclick)
                if m:
                    link_id = m.group(1)
            cell_links.append(link_id)
        
        # Map cells: 순위, 마번, 마명, 산지, 성별, 연령, 중량, 레이팅, 기수명, 조교사명, 마주명, 도착차, 마체중, 단승, 연승, 장구현황
        if len(cell_texts) >= 15:
            # Parse 마체중 - format: "464(-2)"
            weight_raw = cell_texts[12] if len(cell_texts) > 12 else ""
            wm = re.match(r"(\d+)\(([+-]?\d+)\)", weight_raw)
            weight = wm.group(1) if wm else weight_raw
            weight_change = wm.group(2) if wm else ""
            
            horse = {
                "착순": cell_texts[0],
                "출주번호": cell_texts[1],
                "마명": cell_texts[2],
                "마번_link": cell_links[2] if len(cell_links) > 2 else "",
                "산지": cell_texts[3],
                "성별": cell_texts[4],
                "연령": cell_texts[5],
                "부담중량": cell_texts[6],
                "레이팅": cell_texts[7],
                "기수명": cell_texts[8],
                "기수번호": cell_links[8] if len(cell_links) > 8 else "",
                "조교사명": cell_texts[9],
                "조교사번호": cell_links[9] if len(cell_links) > 9 else "",
                "마주명": cell_texts[10],
                "마주번호": cell_links[10] if len(cell_links) > 10 else "",
                "도착차": cell_texts[11],
                "마체중": weight,
                "마체중증감": weight_change,
                "단승배당": cell_texts[13] if len(cell_texts) > 13 else "",
                "연승배당": cell_texts[14] if len(cell_texts) > 14 else "",
                "장구현황": cell_texts[15] if len(cell_texts) > 15 else "",
            }
            horses.append(horse)
    
    # Parse section times table (Table 3 pattern)
    section_data = {}
    if section_table:
        tbody2 = section_table.find("tbody") or section_table
        for tr in tbody2.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 13:
                continue
            cells = [td.get_text(strip=True) for td in tds]
            key = cells[1]  # 출주번호
            
            # cell[2] = 통과순위 (S1F-1C-2C-3C-G3F-4C-G1F in one cell, separated by - and newlines)
            pass_raw = tds[2].get_text(separator="|").strip()
            passes = [p.strip().rstrip("-") for p in re.split(r"[|\n]+", pass_raw) if p.strip() and p.strip() != "\xa0"]
            # pad to 7
            while len(passes) < 7:
                passes.append("")
            
            # cells[3..12] = S1F기록, 1C기록, 2C기록, 3C기록, G3F기록, 4C기록, G1F기록, 3F-G, 1F-G, 경주기록
            section_data[key] = {
                "S1F통과순위": passes[0],
                "1C통과순위": passes[1],
                "2C통과순위": passes[2],
                "3C통과순위": passes[3],
                "G3F통과순위": passes[4],
                "4C통과순위": passes[5],
                "G1F통과순위": passes[6],
                "S1F기록": cells[3] if len(cells) > 3 else "",
                "1C기록": cells[4] if len(cells) > 4 else "",
                "2C기록": cells[5] if len(cells) > 5 else "",
                "3C기록": cells[6] if len(cells) > 6 else "",
                "G3F기록": cells[7] if len(cells) > 7 else "",
                "4C기록": cells[8] if len(cells) > 8 else "",
                "G1F기록": cells[9] if len(cells) > 9 else "",
                "3F_G기록": cells[10] if len(cells) > 10 else "",
                "1F_G기록": cells[11] if len(cells) > 11 else "",
                "경주기록": cells[12] if len(cells) > 12 else "",
            }
    
    # Merge
    for h in horses:
        row = {**race_info, **h}
        sec = section_data.get(h["출주번호"], {})
        for k in ["S1F통과순위", "1C통과순위", "2C통과순위", "3C통과순위", "G3F통과순위", "4C통과순위", "G1F통과순위",
                   "S1F기록", "1C기록", "2C기록", "3C기록", "G3F기록", "4C기록", "G1F기록",
                   "3F_G기록", "1F_G기록", "경주기록"]:
            row[k] = sec.get(k, "")
        rows_out.append(row)
    
    return rows_out


def scrape_month(meet, year, month, writer, csv_file):
    """Scrape all races for a meet/year/month."""
    dates = get_race_dates(meet, year, month)
    total_rows = 0
    
    for rc_date, race_nos in dates:
        for rc_no in race_nos:
            params = {
                "Act": "04", "Sub": "1", "meet": meet,
                "realRcDate": rc_date, "realRcNo": str(rc_no)
            }
            try:
                html = fetch(DETAIL_URL, params)
                rows = parse_detail(html, meet, rc_date, rc_no)
                for r in rows:
                    writer.writerow([r.get(c, "") for c in CSV_COLUMNS])
                total_rows += len(rows)
                csv_file.flush()
            except Exception as e:
                print(f"  ERROR {rc_date} R{rc_no}: {e}", file=sys.stderr)
            
            time.sleep(0.15)  # polite delay
    
    return total_rows


def main():
    # Default: scrape recent 1 year for testing
    import argparse
    parser = argparse.ArgumentParser(description="KRA Race Scraper")
    parser.add_argument("--meet", default="1", help="1=서울, 2=제주, 3=부경")
    parser.add_argument("--from-year", type=int, default=2025)
    parser.add_argument("--from-month", type=int, default=1)
    parser.add_argument("--to-year", type=int, default=2026)
    parser.add_argument("--to-month", type=int, default=3)
    parser.add_argument("--output", default="kra_race_data.csv")
    args = parser.parse_args()
    
    print(f"Scraping {MEETS.get(args.meet, args.meet)} "
          f"from {args.from_year}/{args.from_month:02d} "
          f"to {args.to_year}/{args.to_month:02d}")
    
    with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        
        y, m = args.from_year, args.from_month
        total = 0
        while (y, m) <= (args.to_year, args.to_month):
            print(f"  {y}/{m:02d} ...", end=" ", flush=True)
            n = scrape_month(args.meet, y, m, writer, f)
            print(f"{n} rows")
            total += n
            
            m += 1
            if m > 12:
                m = 1
                y += 1
        
        print(f"\nDone! Total: {total} rows → {args.output}")


if __name__ == "__main__":
    main()
