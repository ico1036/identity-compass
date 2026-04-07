# CIO Review: Round 7 Batch 3, Experiments 0009–0016

**Reviewer**: Critic Agent (Quant CIO)  
**Date**: 2026-04-05  
**Scope**: iTransformer variants, UnifiedTemporalAttention, regularization experiments  
**Prior review**: review_r7_02.md (Verdict: REVISE)

---

## Verdict: FAIL

---

## Executive Summary

After **17 experiments in Round 7**, the mission is **at risk**. Not a single model has shown meaningful regime detection. The attention weights are effectively static across crisis and calm periods. Portfolio weight shifts are measured in **hundredths of a percent**, not the 10-30% that would indicate actual regime awareness.

The Explorer ran 8 experiments in this batch. None addressed the required changes from my previous review. Instead, time was spent on an architecture (UnifiedTemporalAttention) that was dead on arrival.

**The core problem is no longer architectural. It's fundamental: either attention cannot learn regimes from this data at this scale, or the training protocol is broken beyond what architecture can fix.**

---

## Did the Explorer Address My Required Changes?

| Required Change | Status | Notes |
|----------------|--------|-------|
| Diagnose EW gap per-year | ❌ NOT DONE | No per-year comparison produced |
| Investigate MDD | ❌ NOT DONE | No analysis of -42% drawdown |
| iTransformer + entropy reg | ⚠️ PARTIAL | Exp 0013 has both, but no analysis of impact |
| Warm-start training | ❌ NOT DONE | Code prepared, not run |
| Minimum training window | ⚠️ PARTIAL | min_train_samples=1250 in 0013-0016, but not systematically tested |
| Report EW MDD | ❌ NOT DONE | Still no benchmark |

**5 of 6 required changes were ignored.** The Explorer went off-script and experimented with UnifiedTemporalAttention (Exp 0010-0012, 0014-0016) which was not requested and produced the worst results of Round 7.

---

## Experiment-by-Experiment

### Exp 0009: iTransformer d_model=16 (re-run with larger capacity)

**test_sharpe: ~0.88, regime signal: ~0**

More capacity didn't help. Same architecture as 0008, more parameters. No regime signal. No meaningful improvement.

### Exp 0010-0012: UnifiedTemporalAttention Variants

**test_sharpe: 0.47-0.49, regime signal: ~0**

These three experiments represent **wasted effort**. The architecture doesn't work—Sharpe is halved vs iTransformer. The attention is doing something (entropy is non-uniform), but it's not producing useful allocations. The model is learning to dump ~95% into SHY regardless of regime.

**Why was this architecture pursued?** The prior review specifically flagged that iTransformer is "the right direction" and the EW gap needs diagnosis. Instead, 3 experiments were spent on an unproven architecture that failed.

### Exp 0013: iTransformer + Entropy Reg + min_train=1250

**test_sharpe: 0.931, regime signal: max_shift=0.000027**

Best test Sharpe of the batch (0.931). But look at the regime signal: **0.0027% max weight shift between crisis and calm**. This is noise. The model is essentially static.

The entropy regularization (lambda=0.1) produces low attention entropy (1.76), but this doesn't translate to portfolio weight variation. Crisis vs calm weights:
- SPY: 33.26% → 33.26% (change: 0.0027%)
- TLT: 19.93% → 19.93%
- GLD: 26.25% → 26.25%
- SHY: 20.56% → 20.56%

This is equal weight with decimal noise. The entropy reg is making attention sharp, but the attention isn't learning regime-relevant patterns.

### Exp 0014: UnifiedTemporalAttention + entropy lambda=0.05

**test_sharpe: 0.471, regime signal: max_shift=0.01%**

Back to the failed architecture. Even worse than 0013. Crisis weights: 95% SHY. Calm weights: 95% SHY. The model learned "always buy SHY." That's not regime detection—that's risk aversion hardcoded through training dynamics.

### Exp 0015: UnifiedTemporal (no entropy reg)

**test_sharpe: 0.494, regime signal: max_shift=0.0009%**

Control for 0014. Removing entropy reg doesn't help. Architecture is fundamentally flawed for this problem.

### Exp 0016: UnifiedTemporal + diversity penalty

**test_sharpe: 0.881, regime signal: max_shift=0.005%**

Diversity penalty (lambda=0.5) boosts Sharpe from ~0.47 to 0.88—interesting, but still no regime signal. Crisis vs calm weights identical to 4 decimal places.

---

## The Brutal Facts

### 1. ZERO Regime Signal Across 17 Experiments

| Batch | Best Model | test_sharpe | Crisis-Calm Weight Shift |
|-------|-----------|-------------|-------------------------|
| 1 (0000-0004) | Exp 0004 | 0.896 | 2.0% |
| 2 (0005-0008) | Exp 0008 | 0.904 | ~0.0% |
| 3 (0009-0016) | Exp 0013 | 0.931 | 0.0027% |

The best "regime signal" was in Exp 0004 (Batch 1): 2% weight shift. That's economically meaningless. Recent batches: literally zero.

### 2. All Models Cluster at 0.85-0.93 Sharpe

Despite trying:
- Cross-attention (0000-0004)
- Static ablation (0005)
- Patch self-attention (0007)
- iTransformer (0008, 0009, 0013)
- Unified temporal attention (0010-0012, 0014-0016)
- Entropy regularization
- Diversity regularization
- Temperature scaling
- Different d_model sizes

**Everything converges to 0.85-0.93 test_sharpe.** This is not a feature—it's a ceiling. The models are finding the same local optimum: slightly better than static weights, nowhere near regime-aware.

### 3. EW Gap = 0.5 Sharpe (Unchanged)

EW = 1.39. Best model = 0.93. **After 17 experiments, the attention models destroy 33% of EW's risk-adjusted return.** This gap has persisted across every architecture. It is not an architecture problem.

### 4. MDD Remains Unexplained (-40 to -48%)

Exp 0013 improves to -32.4% MDD (better than prior -42%), but this is still worse than static ablation's -31.6%. Attention adds volatility without adding return.

---

## Code Review (train.py)

The code for Exp 0017 (iTransformerEntropy) is prepared but not run. Comments indicate hypothesis about combining best architecture with entropy reg.

Issues with current code:
1. **Attention analysis uses only last model** — same methodological flaw as before. The regime signal reflects a model trained on all data through 2025, not OOS behavior.
2. **No per-year diagnostics** — the infrastructure exists (yearly_results dict) but isn't analyzed.
3. **Missing experiments** — Exp 0017-0021 were planned, only 0017 code exists.

---

## Strategic Assessment: H2 Now 70%

From insights.md:
- **H1**: Attention can work, but training protocol is broken (60% prior)
- **H2**: Attention is wrong approach for this data scale (40% prior)

**Updated belief: 30% H1, 70% H2.**

Evidence for H2:
- 17 experiments, ~8 architectures, 249-916 params
- Zero regime signal in 16 of 17 experiments
- All models hit the same 0.85-0.93 Sharpe ceiling
- EW gap is persistent and unexplained
- Regularization helps Sharpe but not regime detection

If H2 is true, no amount of architecture tweaking will work. The project needs either:
1. More data (daily rebalancing = 3x samples)
2. Different input features
3. Non-attention approach (violates mission)

---

## Required Actions (Mandatory)

The Explorer **must** run Exp 0017-0021 exactly as planned in docs/experiments.md. No new architectures. No deviations.

### Exp 0017: iTransformer + Entropy Reg (code ready)
Run it. Measure crisis-calm diff honestly. If still ~0, report that.

### Exp 0018: Warm-Start Training
Initialize each year's model from prior year's weights. Does regime continuity improve?

### Exp 0019: Minimum Training Window
Don't train until 5+ years of data exist. Skip 2008-2012. Does late-start improve aggregate Sharpe?

### Exp 0020: MDD Investigation
Print weights and returns during max drawdown periods. Diagnose the -42%.

### Exp 0021: EW Gap Diagnosis
Per-year Sharpe comparison: model vs EW. Where does the 0.5 gap come from?

---

## What NOT To Do

1. **No new architectures.** UnifiedTemporalAttention failed. Don't invent another.
2. **No more regularization tuning.** You've tried entropy (0.0, 0.05, 0.1) and diversity (0.5). The problem isn't regularization.
3. **No "creative" experiments.** Follow the plan. The plan was designed to test H1 vs H2.

---

## Questions for the Researcher

1. **17 experiments, zero regime signal.** At what point do you conclude attention doesn't work for this data? What's your threshold for abandoning the approach?

2. **You spent 4 experiments on UnifiedTemporalAttention after I flagged iTransformer as "the right direction."** Why? What hypothesis justified this diversion?

3. **Exp 0013 has the best Sharpe (0.93) and worst regime signal (0.003%).** Is maximizing Sharpe conflicting with learning regimes? If so, should we optimize for regime signal instead?

4. **Why does every model converge to 0.85-0.93 Sharpe?** This convergence suggests a fundamental constraint. What is it?

---

## Final Word

I appreciate the experimental discipline—one change per experiment, clear hypotheses, good code quality. But discipline without direction is just running in place.

**The mission is to learn regimes through attention. After 17 experiments, we have not learned regimes.** The next 5 experiments (0017-0021) are the last chance for H1. If they fail, we must seriously consider that attention is not the right tool for this job.

Run the planned experiments. Report honestly. No more architecture tourism.

**Would I put money in this?** Absolutely not. The best model (0.93 Sharpe) underperforms equal weight by 33% and has no regime awareness. This would lose money in live trading.
