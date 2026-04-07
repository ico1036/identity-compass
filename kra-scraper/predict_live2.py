#!/usr/bin/env python3
"""Live race prediction V2 — POST-based scraping."""

import requests, re, sys, pickle, numpy as np, pandas as pd
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}
MEETS = {"1": "서울", "2": "제주", "3": "부경"}

def get_today_races(meet):
    r = requests.get(f"https://race.kra.co.kr/chulmainfo/ChulmaDetailInfoList.do?Act=02&Sub=1&meet={meet}",
                     headers=HEADERS, timeout=30)
    r.encoding = "euc-kr"
    dates = {}
    for m in re.finditer(r'goChulmapyo\("(\d+)","(\d{8})","(\d+)"\)', r.text):
        mt, d, n = m.group(1), m.group(2), int(m.group(3))
        if mt == meet:
            dates.setdefault(d, []).append(n)
    if not dates:
        return None, []
    latest = max(dates.keys())
    return latest, sorted(set(dates[latest]))

def parse_chulma(meet, date, rc_no):
    r = requests.post("https://race.kra.co.kr/chulmainfo/chulmaDetailInfoChulmapyo.do",
                      data={"meet": meet, "rcDate": date, "rcNo": str(rc_no), "Act": "02", "Sub": "1"},
                      headers=HEADERS, timeout=30)
    r.encoding = "euc-kr"
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Get race info from first tables
    tds_all = [td.get_text(strip=True) for td in soup.find_all("td")]
    distance = 0
    grade = ""
    for t in tds_all:
        dm = re.match(r"^(\d{3,4})M$", t)
        if dm: distance = int(dm.group(1))
        if "등급" in t: grade = t
    
    # Find horse table (번호, 마명, 산지, 성별, 연령, 레이팅, 중량...)
    horses = []
    for table in soup.find_all("table"):
        ths = [th.get_text(strip=True) for th in table.find_all("th")]
        if "마명" in ths and "기수명" in ths:
            for tr in table.find_all("tr")[1:]:  # skip header
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) < 10: continue
                try:
                    # 번호, 마명, 산지, 성별, 연령, 레이팅(증감), 중량, 증감, 기수명, 조교사명, 마주명...
                    rating_raw = cells[5]  # e.g. "34(0)"
                    rm = re.match(r"(\d+)", rating_raw)
                    rating = int(rm.group(1)) if rm else 0
                    
                    h = {
                        "출주번호": int(cells[0]),
                        "마명": cells[1],
                        "산지": "한" if "한국" in cells[2] else "외",
                        "성별": cells[3],
                        "연령": int(cells[4]) if cells[4].isdigit() else 3,
                        "레이팅": rating,
                        "부담중량": float(cells[6]) if cells[6] else 0,
                        "부담증감": float(cells[7]) if cells[7] else 0,
                        "기수명": cells[8],
                        "조교사명": cells[9],
                        "장구": cells[13] if len(cells) > 13 else "",
                    }
                    horses.append(h)
                except Exception as e:
                    continue
            break
    
    return {"경주번호": rc_no, "거리": distance, "등급": grade, "출전마": horses}

def predict_race(race, hist_df, model):
    FEATURES = model.get_booster().feature_names
    성별_map = {"수": 0, "암": 1, "거": 2}
    산지_map = {"한": 0, "외": 1}
    
    grade_str = race.get("등급", "")
    grade_ord = 7
    for g, v in [("1등급",1),("2등급",2),("3등급",3),("4등급",4),("5등급",5),("6등급",6),("오픈",0)]:
        if g in grade_str: grade_ord = v; break
    
    n = len(race["출전마"])
    rows = []
    
    for h in race["출전마"]:
        마명 = h["마명"]
        기수명 = h["기수명"]
        조교사명 = h["조교사명"]
        
        # Historical lookup
        hdf = hist_df[hist_df["마명"] == 마명].copy()
        if len(hdf) > 0:
            hdf["착순_n"] = pd.to_numeric(hdf["착순"], errors="coerce")
            recent = hdf.tail(10)
            착순 = recent["착순_n"].dropna()
            최근3 = 착순.tail(3).mean() if len(착순)>=1 else -1
            최근5 = 착순.tail(5).mean() if len(착순)>=1 else -1
            wins = (착순 == 1)
            최근5승 = wins.tail(5).mean() if len(wins)>=1 else -1
            최근10승 = wins.mean() if len(wins)>=1 else -1
            복승 = (착순 <= 3)
            최근5복 = 복승.tail(5).mean() if len(복승)>=1 else -1
            통산승 = wins.mean()
            통산출주 = len(착순)
            
            def t2s(s):
                try: p=str(s).split(":"); return float(p[0])*60+float(p[1])
                except: return np.nan
            기록 = hdf["경주기록"].apply(t2s) if "경주기록" in hdf.columns else pd.Series(dtype=float)
            최근기록 = 기록.iloc[-1] if len(기록)>0 else -1
            최근3기록 = 기록.tail(3).mean() if len(기록)>=1 else -1
            
            체중 = pd.to_numeric(hdf["마체중"], errors="coerce").dropna()
            체중평균 = 체중.tail(3).mean() if len(체중)>=1 else -1
            
            dates = pd.to_datetime(hdf["경주일자"], errors="coerce").dropna()
            휴양 = (pd.Timestamp.now() - dates.iloc[-1]).days if len(dates)>0 else -1
        else:
            최근3=최근5=최근5승=최근10승=최근5복=통산승=최근기록=최근3기록=체중평균=휴양=-1
            통산출주=0
        
        # Jockey stats
        jdf = hist_df[hist_df["기수명"]==기수명]
        if len(jdf)>0:
            j착 = pd.to_numeric(jdf["착순"], errors="coerce")
            기수승 = (j착==1).mean()
            기수출 = len(j착)
        else:
            기수승=-1; 기수출=-1
        
        tdf = hist_df[hist_df["조교사명"]==조교사명]
        조교사승 = (pd.to_numeric(tdf["착순"],errors="coerce")==1).mean() if len(tdf)>0 else -1
        
        # Distance
        dist = str(race["거리"])
        ddf = hdf[hdf["거리"].astype(str).str.contains(dist)] if len(hdf)>0 and "거리" in hdf.columns else pd.DataFrame()
        거리승 = (pd.to_numeric(ddf["착순"],errors="coerce")==1).mean() if len(ddf)>0 else -1
        거리출 = len(ddf)
        
        row = {
            "연령_num": h["연령"], "성별_enc": 성별_map.get(h["성별"],-1),
            "산지_enc": 산지_map.get(h["산지"],-1), "부담중량": h["부담중량"],
            "마체중": -1, "마체중증감": 0, "장구_count": len([x for x in h["장구"].split(",") if x.strip()]),
            "거리_num": race["거리"], "등급_ord": grade_ord, "별정_enc": 0,
            "경주번호": race["경주번호"], "출전두수": n, "날씨_enc": 0, "주로상태_enc": 0, "함수율": -1,
            "단승배당": -1, "연승배당": -1, "시장확률": -1, "배당순위": -1,
            "최근3전_평균착순": 최근3, "최근5전_평균착순": 최근5,
            "최근5전_승률": 최근5승, "최근10전_승률": 최근10승, "최근5전_복승률": 최근5복,
            "통산_승률": 통산승, "통산_출주수": 통산출주,
            "체중_3회이동평균": 체중평균, "체중_트렌드": 0, "체중순위": -1,
            "최근_경주기록": 최근기록, "최근3전_평균기록": 최근3기록, "최근3전_G3F": -1,
            "기수_누적승률": 기수승, "기수_누적출주": 기수출, "조교사_누적승률": 조교사승,
            "거리별_승률": 거리승, "거리별_출주수": 거리출,
            "콤비_승률": -1, "콤비_출주수": -1, "휴양일수": 휴양,
        }
        rows.append((h, row))
    
    df = pd.DataFrame([r[1] for r in rows])
    X = df[FEATURES].fillna(-1)
    probs = model.predict_proba(X)[:, 1]
    probs_norm = probs / probs.sum()
    
    results = []
    for i, (h, _) in enumerate(rows):
        results.append({"번호": h["출주번호"], "마명": h["마명"], "prob": probs_norm[i],
                        "raw": probs[i], "기수": h["기수명"]})
    results.sort(key=lambda x: -x["prob"])
    return results

def main():
    meet = sys.argv[1] if len(sys.argv) > 1 else "1"
    print(f"Loading model & data...")
    model = pickle.load(open("model_win.pkl", "rb"))
    hist_df = pd.read_csv("kra_seoul_final.csv", encoding="utf-8-sig", dtype=str)
    
    date, race_nos = get_today_races(meet)
    if not race_nos:
        print(f"오늘 {MEETS.get(meet,meet)} 경주 없음!"); return
    
    print(f"\n🏇 {MEETS.get(meet,meet)} {date} — {len(race_nos)}경주 예측\n")
    
    all_picks = []
    for rc_no in race_nos:
        race = parse_chulma(meet, date, rc_no)
        if not race["출전마"]:
            print(f"  {rc_no}R — 파싱 실패"); continue
        
        results = predict_race(race, hist_df, model)
        dist = race["거리"]
        grade = race["등급"]
        
        print(f"━━ {rc_no}R | {grade} | {dist}M | {len(race['출전마'])}두 ━━")
        for rank, r in enumerate(results[:5], 1):
            star = "⭐" if rank <= 3 else "  "
            print(f" {star}{rank}. #{r['번호']:<2} {r['마명']:<12} ({r['기수']:<6}) {r['prob']:>6.1%}")
        
        top = results[0]
        fair = 1/top["prob"]
        all_picks.append(f"#{top['번호']} {top['마명']} ({top['prob']:.0%}, 적정{fair:.1f}배)")
        print()
    
    print(f"{'━'*50}")
    print(f"💰 경주별 TOP PICK:")
    for i, (rc, pick) in enumerate(zip(race_nos, all_picks)):
        print(f"  {rc}R → {pick}")

if __name__ == "__main__":
    main()
