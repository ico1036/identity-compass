#!/usr/bin/env python3
"""Live race prediction — scrape 출전표 from race.kra.co.kr and predict."""

import requests
import re
import sys
import pickle
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
MEETS = {"1": "서울", "2": "제주", "3": "부경"}

def fetch(url, params=None):
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    r.encoding = "euc-kr"
    return r.text

def get_today_races(meet):
    """Get list of race numbers for today."""
    html = fetch(f"https://race.kra.co.kr/chulmainfo/ChulmaDetailInfoList.do?Act=02&Sub=1&meet={meet}")
    races = []
    today = None
    for m in re.finditer(r'goChulmapyo\("(\d+)","(\d{8})","(\d+)"\)', html):
        mt, date, rno = m.group(1), m.group(2), int(m.group(3))
        if mt == meet:
            if today is None or date >= today:
                today = date
            if date == today:
                races.append(rno)
    # Deduplicate but keep order
    seen = set()
    result = []
    for r in races:
        if r not in seen:
            seen.add(r)
            result.append(r)
    return today, sorted(result)

def parse_chulma(meet, date, rc_no):
    """Parse 출전상세정보 for a single race."""
    url = "https://race.kra.co.kr/chulmainfo/ChulmaDetailInfoList.do"
    params = {"Act": "02", "Sub": "1", "meet": meet, "realRcDate": date, "realRcNo": str(rc_no)}
    html = fetch(url, params)
    soup = BeautifulSoup(html, "html.parser")
    
    # Race info
    tds = soup.find_all("td")
    td_texts = [td.get_text(strip=True) for td in tds]
    
    distance = ""
    grade = ""
    for t in td_texts:
        if re.match(r"\d+M$", t):
            distance = int(t.replace("M", ""))
        if "등급" in t:
            grade = t
    
    # Parse horse table
    tables = soup.find_all("table")
    horses = []
    
    for table in tables:
        ths = [th.get_text(strip=True) for th in table.find_all("th")]
        if "마명" in ths and ("부담" in " ".join(ths) or "중량" in " ".join(ths)):
            tbody = table.find("tbody") or table
            for tr in tbody.find_all("tr"):
                cells = tr.find_all("td")
                if len(cells) < 8:
                    continue
                
                cell_texts = [c.get_text(strip=True) for c in cells]
                
                # Extract jockey/trainer IDs from links
                jockey_name = ""
                trainer_name = ""
                for c in cells:
                    a = c.find("a")
                    if a:
                        onclick = a.get("onclick", "")
                        if "goJockey" in onclick or "Jockey" in onclick:
                            jockey_name = a.get_text(strip=True)
                        elif "goTrainer" in onclick or "Trainer" in onclick:
                            trainer_name = a.get_text(strip=True)
                
                # Try to extract key fields
                # Typical order varies, but look for patterns
                horse = {"raw": cell_texts}
                
                # Find 마번 (number)
                for i, t in enumerate(cell_texts):
                    if re.match(r"^\d{1,2}$", t) and i < 3:
                        horse["출주번호"] = int(t)
                        break
                
                # Find 마명 (has link usually)
                for c in cells:
                    a = c.find("a")
                    if a:
                        onclick = a.get("onclick", "")
                        if "goHorse" in onclick or "Horse" in onclick:
                            horse["마명"] = a.get_text(strip=True)
                
                if "마명" not in horse:
                    continue
                
                # Extract other fields by position/pattern
                for t in cell_texts:
                    if re.match(r"\d{1,2}세$", t):
                        horse["연령"] = int(t.replace("세", ""))
                    if t in ("수", "암", "거"):
                        horse["성별"] = t
                    if t in ("한", "외"):
                        horse["산지"] = t
                    if re.match(r"^\d{2,3}(\.\d)?$", t) and float(t) > 40 and float(t) < 65:
                        horse["부담중량"] = float(t)
                    # 마체중 pattern: 465(+3) or 465(-2)
                    wm = re.match(r"(\d{3,4})\(([+-]?\d+)\)", t)
                    if wm:
                        horse["마체중"] = int(wm.group(1))
                        horse["마체중증감"] = int(wm.group(2))
                
                if jockey_name:
                    horse["기수명"] = jockey_name
                if trainer_name:
                    horse["조교사명"] = trainer_name
                
                horses.append(horse)
    
    return {
        "경주번호": rc_no,
        "거리": distance,
        "등급": grade,
        "출전마": horses,
    }


def build_features(race, historical_df=None):
    """Build feature matrix for prediction."""
    model = pickle.load(open("model_win.pkl", "rb"))
    FEATURES = model.get_booster().feature_names
    
    성별_map = {"수": 0, "암": 1, "거": 2}
    산지_map = {"한": 0, "외": 1}
    
    grade_str = race.get("등급", "")
    grade_ord = 7
    for g, v in [("1등급", 1), ("2등급", 2), ("3등급", 3), ("4등급", 4), ("5등급", 5), ("6등급", 6), ("오픈", 0)]:
        if g in grade_str:
            grade_ord = v
            break
    
    n_horses = len(race["출전마"])
    rows = []
    
    for h in race["출전마"]:
        # Look up historical data
        마명 = h.get("마명", "")
        hist = None
        if historical_df is not None and 마명:
            hist = historical_df[historical_df["마명"] == 마명].sort_values("경주일자")
        
        # Compute historical features
        if hist is not None and len(hist) > 0:
            recent = hist.tail(10)
            착순_vals = pd.to_numeric(recent["착순"], errors="coerce").dropna()
            wins = (착순_vals == 1)
            places = (착순_vals <= 3)
            
            최근3전_평균착순 = 착순_vals.tail(3).mean() if len(착순_vals) >= 1 else -1
            최근5전_평균착순 = 착순_vals.tail(5).mean() if len(착순_vals) >= 1 else -1
            최근5전_승률 = wins.tail(5).mean() if len(wins) >= 1 else -1
            최근10전_승률 = wins.mean() if len(wins) >= 1 else -1
            최근5전_복승률 = places.tail(5).mean() if len(places) >= 1 else -1
            통산_승률 = wins.mean()
            통산_출주수 = len(착순_vals)
            
            # Time
            기록 = hist["경주기록_sec"] if "경주기록_sec" in hist.columns else pd.Series(dtype=float)
            if "경주기록" in hist.columns:
                def t2s(s):
                    try:
                        p = str(s).split(":")
                        return float(p[0])*60 + float(p[1])
                    except:
                        return np.nan
                기록 = hist["경주기록"].apply(t2s)
            
            최근_경주기록 = 기록.iloc[-1] if len(기록) > 0 and not np.isnan(기록.iloc[-1]) else -1
            최근3전_평균기록 = 기록.tail(3).mean() if len(기록) >= 1 else -1
            
            # Weight trend
            체중s = pd.to_numeric(hist["마체중"], errors="coerce").dropna()
            체중_3회이동평균 = 체중s.tail(3).mean() if len(체중s) >= 1 else -1
            
            # Jockey/trainer from historical
            기수명 = h.get("기수명", "")
            if 기수명 and historical_df is not None:
                j_hist = historical_df[historical_df["기수명"] == 기수명]
                j_wins = (pd.to_numeric(j_hist["착순"], errors="coerce") == 1)
                기수_누적승률 = j_wins.mean() if len(j_wins) > 0 else -1
                기수_누적출주 = len(j_wins)
            else:
                기수_누적승률 = -1
                기수_누적출주 = -1
            
            조교사명 = h.get("조교사명", "")
            if 조교사명 and historical_df is not None:
                t_hist = historical_df[historical_df["조교사명"] == 조교사명]
                t_wins = (pd.to_numeric(t_hist["착순"], errors="coerce") == 1)
                조교사_누적승률 = t_wins.mean() if len(t_wins) > 0 else -1
            else:
                조교사_누적승률 = -1
            
            # Distance affinity
            dist = race.get("거리", 0)
            if dist and historical_df is not None:
                d_hist = hist[hist["거리"].astype(str).str.contains(str(dist))] if "거리" in hist.columns else pd.DataFrame()
                if len(d_hist) > 0:
                    d_wins = (pd.to_numeric(d_hist["착순"], errors="coerce") == 1)
                    거리별_승률 = d_wins.mean()
                    거리별_출주수 = len(d_wins)
                else:
                    거리별_승률 = -1
                    거리별_출주수 = 0
            else:
                거리별_승률 = -1
                거리별_출주수 = 0
            
            # Rest days
            dates = pd.to_datetime(hist["경주일자"], errors="coerce").dropna()
            if len(dates) > 0:
                last_race = dates.iloc[-1]
                휴양일수 = (pd.Timestamp.now() - last_race).days
            else:
                휴양일수 = -1
        else:
            # No historical data
            최근3전_평균착순 = -1
            최근5전_평균착순 = -1
            최근5전_승률 = -1
            최근10전_승률 = -1
            최근5전_복승률 = -1
            통산_승률 = -1
            통산_출주수 = 0
            최근_경주기록 = -1
            최근3전_평균기록 = -1
            체중_3회이동평균 = -1
            기수_누적승률 = -1
            기수_누적출주 = -1
            조교사_누적승률 = -1
            거리별_승률 = -1
            거리별_출주수 = 0
            휴양일수 = -1
        
        마체중 = h.get("마체중", -1)
        마체중증감 = h.get("마체중증감", 0)
        
        row = {
            "연령_num": h.get("연령", -1),
            "성별_enc": 성별_map.get(h.get("성별", ""), -1),
            "산지_enc": 산지_map.get(h.get("산지", ""), -1),
            "부담중량": h.get("부담중량", -1),
            "마체중": 마체중,
            "마체중증감": 마체중증감,
            "장구_count": 0,
            "거리_num": race.get("거리", -1),
            "등급_ord": grade_ord,
            "별정_enc": 0,
            "경주번호": race.get("경주번호", -1),
            "출전두수": n_horses,
            "날씨_enc": 0,
            "주로상태_enc": 0,
            "함수율": -1,
            "단승배당": -1,
            "연승배당": -1,
            "시장확률": -1,
            "배당순위": -1,
            "최근3전_평균착순": 최근3전_평균착순,
            "최근5전_평균착순": 최근5전_평균착순,
            "최근5전_승률": 최근5전_승률,
            "최근10전_승률": 최근10전_승률,
            "최근5전_복승률": 최근5전_복승률,
            "통산_승률": 통산_승률,
            "통산_출주수": 통산_출주수,
            "체중_3회이동평균": 체중_3회이동평균,
            "체중_트렌드": 마체중증감,
            "체중순위": -1,
            "최근_경주기록": 최근_경주기록,
            "최근3전_평균기록": 최근3전_평균기록,
            "최근3전_G3F": -1,
            "기수_누적승률": 기수_누적승률,
            "기수_누적출주": 기수_누적출주,
            "조교사_누적승률": 조교사_누적승률,
            "거리별_승률": 거리별_승률,
            "거리별_출주수": 거리별_출주수,
            "콤비_승률": -1,
            "콤비_출주수": -1,
            "휴양일수": 휴양일수,
        }
        rows.append((h, row))
    
    # Build DataFrame
    feature_rows = [r[1] for r in rows]
    df = pd.DataFrame(feature_rows)
    
    # Relative features
    if "마체중" in df.columns and (df["마체중"] > 0).any():
        df["체중순위"] = df["마체중"].replace(-1, np.nan).rank(method="min")
    
    X = df[FEATURES].fillna(-1)
    
    # Predict
    probs = model.predict_proba(X)[:, 1]
    probs_norm = probs / probs.sum()
    
    results = []
    for i, (h, _) in enumerate(rows):
        results.append({
            "번호": h.get("출주번호", i+1),
            "마명": h.get("마명", f"마{i+1}"),
            "prob": probs_norm[i],
            "raw": probs[i],
            "기수": h.get("기수명", "?"),
        })
    
    results.sort(key=lambda x: -x["prob"])
    return results


def main():
    meet = sys.argv[1] if len(sys.argv) > 1 else "1"
    meet_name = MEETS.get(meet, meet)
    
    print(f"Loading model...")
    model = pickle.load(open("model_win.pkl", "rb"))
    
    print(f"Loading historical data...")
    hist_df = pd.read_csv("kra_seoul_final.csv", encoding="utf-8-sig", dtype=str)
    
    print(f"Fetching today's {meet_name} races...")
    date, race_nos = get_today_races(meet)
    
    if not race_nos:
        print(f"오늘 {meet_name} 경주가 없습니다!")
        return
    
    print(f"날짜: {date}, {len(race_nos)}경주\n")
    print("=" * 55)
    
    for rc_no in race_nos:
        print(f"\n{'━' * 55}")
        print(f"  {meet_name} {rc_no}R", end="")
        
        try:
            race = parse_chulma(meet, date, rc_no)
            if not race["출전마"]:
                print(" — 출전마 파싱 실패")
                continue
            
            dist = race.get("거리", "?")
            grade = race.get("등급", "?")
            n = len(race["출전마"])
            print(f" | {grade} | {dist}M | {n}두")
            print(f"{'━' * 55}")
            
            results = build_features(race, hist_df)
            
            print(f"{'순위':>3} {'번호':>3} {'마명':<14} {'기수':<8} {'승률':>7}")
            print(f"{'-'*45}")
            for rank, r in enumerate(results, 1):
                star = "⭐" if rank <= 3 else "  "
                print(f"{star}{rank:>1}  #{r['번호']:<3} {r['마명']:<14} {r['기수']:<8} {r['prob']:>6.1%}")
            
            # Betting line
            top = results[0]
            fair = 1 / top["prob"]
            print(f"\n  💰 추천: #{top['번호']} {top['마명']} (적정배당 {fair:.1f}배)")
            
        except Exception as e:
            print(f" — 에러: {e}")
    
    print(f"\n{'━' * 55}")
    print(f"⚠️ 배당률 없이 순수 실력 기반 예측")


if __name__ == "__main__":
    main()
