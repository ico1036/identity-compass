"""
Pool Disagreement Strategy v1
- 단승 rank vs 연승 rank 비교
- rank_diff ≤ -2 이상 괴리 → 연승 베팅 (historical ROI +13~160%)
- 복연/삼복은 시그널 말들 조합으로 구성
- Kelly Criterion 적용
"""
import sys
import json

def analyze(odds_data, total_budget):
    """
    odds_data: list of {num, name, dansng, yeonsung}
    """
    # Rank by 단승 and 연승
    by_dan = sorted(odds_data, key=lambda x: x['dansung'])
    by_yeon = sorted(odds_data, key=lambda x: x['yeonsung'])
    
    for i, h in enumerate(by_dan):
        h['dan_rank'] = i + 1
    
    yeon_rank_map = {h['num']: i+1 for i, h in enumerate(by_yeon)}
    for h in odds_data:
        h['yeon_rank'] = yeon_rank_map[h['num']]
        h['rank_diff'] = h['dan_rank'] - h['yeon_rank']
    
    print("=" * 60)
    print("POOL DISAGREEMENT ANALYSIS")
    print("=" * 60)
    print(f"{'번호':>4} {'마명':>8} {'단승':>6} {'연승':>6} {'단R':>4} {'연R':>4} {'차이':>4} {'시그널':>6}")
    print("-" * 60)
    
    signals = []
    for h in sorted(odds_data, key=lambda x: x['dan_rank']):
        sig = ""
        if h['rank_diff'] <= -3:
            sig = "🔥🔥🔥"
        elif h['rank_diff'] <= -2:
            sig = "🔥🔥"
        elif h['rank_diff'] >= 2 and h['yeon_rank'] <= 3:
            sig = "⚠️TRAP"  # 연승 인기 > 단승 → historically -34% ROI
        
        print(f"  {h['num']:>2}  {h.get('name',''):>8} {h['dansung']:>6.1f} {h['yeonsung']:>6.1f} {h['dan_rank']:>4} {h['yeon_rank']:>4} {h['rank_diff']:>+4} {sig}")
        
        if h['rank_diff'] <= -2:
            signals.append(h)
    
    print(f"\n{'=' * 60}")
    print(f"SIGNALS (rank_diff ≤ -2): {len(signals)}마리")
    print(f"{'=' * 60}")
    
    if not signals:
        print("⚠️ 시그널 없음! 이 레이스는 패스 추천.")
        # Fallback: just bet top 2 favorites
        print("\nFallback: 단승 1-2위 인기마 연승")
        top2 = sorted(odds_data, key=lambda x: x['dansung'])[:2]
        for h in top2:
            print(f"  ⓪{h['num']} 연승 {h['yeonsung']}배")
        return
    
    # Kelly sizing for 연승 bets on signal horses
    # Historical stats by rank_diff:
    # -2: hit 23.3%, -3: hit 24.5%, -4: hit 28.2%, -5: hit 31.7%
    hit_rates = {-2: 0.233, -3: 0.245, -4: 0.282, -5: 0.317}
    
    print(f"\n총 예산: {total_budget:,}원")
    print(f"\n--- 연승 베팅 (핵심) ---")
    
    bets = []
    total_alloc = 0
    
    for h in signals:
        rd = max(int(h['rank_diff']), -5)
        p = hit_rates.get(rd, hit_rates[-2])
        odds = h['yeonsung']
        
        # Half Kelly
        b = odds - 1
        if b <= 0:
            continue
        f = (b * p - (1 - p)) / (2 * b)
        if f <= 0:
            print(f"  ⓪{h['num']}: 연승 {odds}배, edge 없음 (Kelly ≤ 0)")
            continue
        
        amount = int(f * total_budget / 100) * 100  # round to 100
        amount = max(amount, 100)
        amount = min(amount, int(total_budget * 0.3))  # cap 30%
        
        edge = (odds * p - 1) * 100
        bets.append({'num': h['num'], 'type': '연승', 'odds': odds, 'amount': amount, 'edge': edge, 'rank_diff': h['rank_diff']})
        total_alloc += amount
        print(f"  ⓪{h['num']}: 연승 {odds}배, edge {edge:+.0f}%, Kelly {f:.1%} → {amount:,}원")
    
    # Also generate 복연 combos with signal horses + top favorites
    top3_fav = sorted(odds_data, key=lambda x: x['dansung'])[:3]
    sig_nums = set(h['num'] for h in signals)
    top3_nums = set(h['num'] for h in top3_fav)
    
    # 복연 combos: signal horse × top favorite
    print(f"\n--- 복연 추천 (시그널 × 인기마) ---")
    bok_budget = total_budget * 0.3
    bok_combos = []
    for s in signals:
        for t in top3_fav:
            if s['num'] != t['num']:
                combo = tuple(sorted([s['num'], t['num']]))
                if combo not in [c['combo'] for c in bok_combos]:
                    bok_combos.append({'combo': combo, 'sig_odds': s['yeonsung'], 'fav_odds': t['yeonsung']})
    
    if bok_combos:
        per_combo = int(bok_budget / len(bok_combos) / 100) * 100
        per_combo = max(per_combo, 100)
        for bc in bok_combos:
            a, b = bc['combo']
            amount = per_combo
            bets.append({'num': f"{a}/{b}", 'type': '복연', 'odds': '?', 'amount': amount})
            total_alloc += amount
            print(f"  {a}/{b} 복연 → {amount:,}원")
    
    print(f"\n{'=' * 60}")
    print(f"총 배팅: {total_alloc:,}원 / {total_budget:,}원 ({total_alloc/total_budget:.0%})")
    print(f"잔여: {total_budget - total_alloc:,}원")
    print(f"{'=' * 60}")
    
    return bets

if __name__ == '__main__':
    # Test with Seoul 7R data (the race we just lost)
    test_data = [
        {'num': 1, 'name': '', 'dansung': 8.2, 'yeonsung': 2.8},
        {'num': 2, 'name': '', 'dansung': 5.5, 'yeonsung': 2.8},
        {'num': 3, 'name': '', 'dansung': 4.5, 'yeonsung': 1.1},
        {'num': 4, 'name': '', 'dansung': 3.3, 'yeonsung': 1.6},
        {'num': 5, 'name': '', 'dansung': 22.5, 'yeonsung': 4.3},
        {'num': 6, 'name': '', 'dansung': 18.1, 'yeonsung': 4.8},
        {'num': 7, 'name': '', 'dansung': 7.2, 'yeonsung': 2.3},
        {'num': 8, 'name': '', 'dansung': 18.3, 'yeonsung': 4.8},
        {'num': 9, 'name': '', 'dansung': 30.2, 'yeonsung': 5.0},
        {'num': 10, 'name': '', 'dansung': 10.5, 'yeonsung': 3.3},
    ]
    
    print("=== 서울 7R 역검증 (결과: ②③④) ===\n")
    analyze(test_data, 22400)
