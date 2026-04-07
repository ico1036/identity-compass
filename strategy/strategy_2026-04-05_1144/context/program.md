# Program

Read `docs/philosophy.md` first. THE MISSION is non-negotiable.

## Architecture: 2-Agent Autonomous Loop

```
┌─────────────────────────────────────────────────┐
│                  CRON (15min)                    │
│  Reads state files → spawns correct agent       │
├─────────────────────────────────────────────────┤
│                                                 │
│  State: NEEDS_CRITIC exists?                    │
│    YES → spawn Critic                           │
│    NO  → LOCK exists?                           │
│           YES → skip (agent running)            │
│           NO  → spawn Explorer                  │
│                                                 │
│  LOCK older than 2hr? → delete (stale)          │
│                                                 │
└─────────────────────────────────────────────────┘

Explorer (5 experiments)          Critic (review)
┌──────────────────────┐         ┌──────────────────────┐
│ 1. Acquire LOCK      │         │ 1. Acquire LOCK      │
│ 2. Read docs/*       │         │ 2. Read docs/critic.md│
│ 3. Run 5 experiments │         │ 3. Read last 5 cards  │
│ 4. Update experiments│         │ 4. Read train.py      │
│    .md + insights.md │         │ 5. Write review to    │
│ 5. git commit + push │         │    docs/reviews/      │
│ 6. Create            │         │ 6. If REVISE/FAIL:    │
│    NEEDS_CRITIC      │         │    update insights.md │
│ 7. Remove LOCK       │         │ 7. git commit + push  │
│ 8. EXIT              │         │ 8. Remove NEEDS_CRITIC│
└──────────────────────┘         │ 9. Remove LOCK        │
                                 │ 10. EXIT              │
                                 └──────────────────────┘
```

Main agent (주인님과 대화하는 세션) is **NEVER in the loop**. It only monitors.

## State Files (in repo root)

| File | Meaning | Created by | Removed by |
|------|---------|------------|------------|
| `LOCK` | An agent is running | Explorer or Critic | Same agent on exit |
| `NEEDS_CRITIC` | 5 experiments done, awaiting review | Explorer | Critic |

## THE RULE

**Every experiment MUST use an attention-based model that preserves the time dimension.**

- No mean/sum/last pooling over time BEFORE the attention layer.
- Attention must see sequential time steps (patches, raw days, etc.).
- MLP, Linear, MinVar are BENCHMARKS computed in prepare.py. You don't build them. You compare against them.
- If your attention model scores lower than a benchmark: that's information. Fix the model. Do NOT switch to the benchmark.

## Lock Protocol
```bash
if [ -f LOCK ]; then echo "LOCKED — another agent is running"; exit 1; fi
echo "$(date) — $(hostname)" > LOCK
trap 'rm -f LOCK' EXIT  # always clean up
```

## Setup (once per session)
```bash
uv sync
uv run prepare.py   # builds tensors from parquet, ~10s
```

---

# Explorer Agent Instructions

## Experiment Loop

1. Read `docs/philosophy.md`, `docs/insights.md`, `docs/experiments.md`.
2. **Check for Critic feedback**: Read latest `docs/reviews/review_*.md`. If verdict was REVISE or FAIL, address ALL required changes first.
3. Form a hypothesis about how attention can learn regimes. Write it at the top of `train.py`:
   ```python
   # Hypothesis: PatchTST with 5-day patches lets attention see weekly patterns
   # Expected: val_sharpe [0.3, 1.0], train_time [60, 300]
   # Regime check: attention weights should differ between 2008 crisis and 2017 calm
   ```
4. Modify `train.py`. The model MUST have attention over a time axis.
5. Run: `uv run guard.py` (never train.py directly).
6. Record in `docs/experiments.md`:
   ```
   ## Exp N: [description]
   - Hypothesis: ...
   - Architecture: [attention type, d_model, n_heads, patch_size]
   - val_sharpe: X.XX | test_sharpe: X.XX | params: XXX
   - Regime signal: [crisis entropy vs calm entropy, weight shift magnitude]
   - Verdict: KEEP / DISCARD
   ```
7. KEEP: continue. DISCARD: `git checkout HEAD -- train.py`.
8. After 5 experiments → go to Exit Protocol.

## What train.py Must Do

```python
from prepare import (
    load_data, make_samples, split_data,
    evaluate_and_print, write_card,
    N_ASSETS, REBAL_FREQ, MAX_PARAMS,
)
```

1. Load data via `load_data()`, create samples via `make_samples()`.
2. Build features from raw price data (NO collapsing time axis).
3. Define an attention-based model.
4. Train with Sharpe loss (or CVaR, Sortino — your choice).
5. Evaluate with `evaluate_and_print()`.
6. Write card with `write_card()`. Include `regime_signal` in config.
7. NEVER redefine sharpe/sortino/MDD. Use prepare.py's versions.

## Exit Protocol (mandatory — after 5 experiments OR session time limit)

```bash
# 1. Update docs
# Update docs/experiments.md with all results
# Update docs/insights.md with learnings

# 2. Commit
git add -A && git commit -m "explorer: exp N-M complete" && git push

# 3. Signal Critic
echo "$(date)" > NEEDS_CRITIC

# 4. Clean up (trap should handle, but be explicit)
rm -f LOCK
```

**Then EXIT. Do not run more experiments. Do not spawn anything.**

## Session Limits
- **5 experiments per session**, then exit.
- Always follow Exit Protocol.
- If you hit a time limit before 5 experiments, still follow Exit Protocol with however many you completed.

---

# Critic Agent Instructions

## Your Job

You are spawned by cron when `NEEDS_CRITIC` exists. You are a **different agent** from the Explorer. You have fresh eyes.

1. Acquire LOCK.
2. Read `docs/critic.md` for your persona and review process.
3. Read `docs/philosophy.md` for THE MISSION.
4. Read `docs/experiments.md` for recent results.
5. Read all cards in `cards/` from the last batch.
6. Read `train.py` — the actual code.
7. Read latest review in `docs/reviews/` if any (for continuity).
8. Write your CIO Review to `docs/reviews/review_rN_MM.md` following critic.md format.
9. If REVISE or FAIL: update `docs/insights.md` with required changes for Explorer.
10. `git add -A && git commit -m "critic: review rN_MM — [VERDICT]" && git push`
11. Remove `NEEDS_CRITIC`.
12. Remove LOCK.
13. EXIT.

## Review Numbering
- `review_r7_01.md` = Round 7, review batch 1
- `review_r7_02.md` = Round 7, review batch 2
- Check existing reviews to pick the next number.

---

## Self-Diagnosis (Explorer — before every experiment)
- Read `docs/insights.md` first.
- If val-test gap > 1.5: overfitting → reduce model or add regularization.
- If training finishes in < 30s with >0 params: data pipeline or model too small.
- If attention weights are static across all periods: the model isn't learning regimes. Change architecture.
- NEVER give up on attention. If stuck, GET CREATIVE:
  - Invent new attention variants (sparse, linear, cross-attention, prototype queries)
  - Hybrid architectures (state-space + attention gate, conv + attention)
  - Novel input representations (signatures, wavelet patches, learned tokenization)
  - Unconventional losses (contrastive regime loss, attention entropy regularization)
  - The constraint is "attention over time for regime learning." HOW is wide open.

## Socratic Self-Check (before committing to any new model direction)

Before implementing a new architecture or major design change, interrogate yourself:

1. **인풋 데이터의 여정을 말해봐.** Raw data → model → output까지 한 단계씩 설명. 설명 못 하면 이해 못 한 거다.
2. **피처는 뭐야?** 각 차원이 뭘 뜻하는지 명확히. "17차원"이면 왜 17인지.
3. **데이터포인트는 몇 개야?** 자산을 독립 취급했는가? 안 했으면 왜?
4. **시계열 학습이 되는 구조야?** 시간축이 mean/sum으로 사라지지 않았는가?
5. **이 설계의 전제는 뭐야?** 그 전제가 philosophy.md의 미션과 일치하는가?

이 질문에 명쾌하게 답할 수 없으면 코딩하지 마라. 먼저 생각하라.

## Dream Phase (every 10 experiments)

1. Read all cards and `docs/experiments.md`.
2. **Mission check**: How many experiments actually had attention over time? If < 100%, explain why and fix.
3. **Regime check**: In the best model so far, do attention weights change meaningfully across market periods? If not, what's missing?
4. Extract patterns. Generate 3 new hypotheses for how attention can capture regimes.
5. Update `docs/insights.md` with:
   - Mission progress (not just Sharpe numbers)
   - Best regime signal observed so far
   - Next hypotheses

## Rules
- Only modify `train.py`. Never touch `prepare.py` or `guard.py`.
- Max 25K parameters.
- Device: MPS (Apple Silicon).
- Walk-forward: train on past, test on future. No shuffling.
- Reproducible (set seed).
- New libraries: `uv add <package>` first.

## What to Explore
- Patch sizes (3, 5, 10, 20 days)
- Attention order: temporal→spatial, spatial→temporal, interleaved
- d_model (8, 16, 32), heads (1, 2, 4)
- Loss: -Sharpe, CVaR, Sortino, -Sharpe + turnover penalty
- Input: raw returns, normalized returns, return + vol features
- Position encoding: RoPE, learned, sinusoidal, none
- Data augmentation if samples insufficient
- Rebalancing frequency changes (daily for more samples)
