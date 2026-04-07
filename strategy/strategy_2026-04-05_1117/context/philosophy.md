# Philosophy

## THE MISSION (inviolable)

**Build an attention-based model that implicitly learns market regimes through its attention weights and outputs optimal asset allocation weights end-to-end.**

This is the entire reason this project exists. Everything below serves this mission.

### What this means concretely:
1. The model MUST contain attention mechanism(s).
2. Attention weights MUST operate over a time dimension (not collapsed by mean/sum).
3. The model takes raw time-series as input and outputs portfolio weights via softmax.
4. Regime detection is implicit — encoded in how attention weights shift over time. No categorical regime labels.
5. The model must learn WHEN to allocate WHERE — temporal dynamics, not static feature averages.

### What is NOT acceptable:
- Models without attention (MLP, Linear, MinVar, etc.) are BENCHMARKS, not solutions.
- A benchmark beating the attention model does NOT mean "give up on attention." It means the attention model needs more work.
- Collapsing the time axis (mean, sum, last) before the attention layer defeats the purpose. The attention must SEE the time series.
- Declaring the project "solved" by a non-attention method.

### Creativity is encouraged:
- You are NOT limited to vanilla Transformer attention. Invent new attention variants if needed.
- Cross-attention, sparse attention, linear attention, state-space hybrids with attention gates, learned query prototypes — anything goes as long as the core mechanism attends over time and learns regime-like patterns.
- If standard approaches hit a wall, THINK DIFFERENTLY. The goal is regime-aware allocation via learned temporal attention — how you get there is open.

## 단순함의 미학 (under the mission)

**핵심만 사용하고 군더더기가 없어야 한다.**

- 아이디어 하나에 코드 변경 하나. 한 실험에 3가지를 동시에 바꾸지 마라.
- 새 레이어를 추가하려면 기존 레이어를 제거할 이유를 먼저 대라.
- 창의성 = 복잡한 코드가 아니라 본질적인 관찰. 10줄로 된 핵심 아이디어가 100줄 엔지니어링을 이긴다.
- 모델 코드가 100줄을 넘으면 의심하라. 진짜 필요한 게 뭔지 다시 생각하라.

구체적으로:
1. **≤25K params**. 데이터가 부족하면 모델을 키우지 말고 데이터를 늘려라.
2. **Price-based features only**. 매크로 지표 금지.
3. **Dual Attention** (spatial + temporal)을 탐색하되, 둘 다 필요한지 실험으로 증명하라.
4. **Patching**: 시간 압축의 가장 단순한 방법.

## Data Scarcity is a Problem to SOLVE, Not a Reason to Quit

If 839 samples aren't enough for attention to learn:
- Increase rebalancing frequency (daily = ~3100 samples)
- Expand asset universe (more cross-sectional variation)
- Data augmentation (noise injection, bootstrap, time-shift)
- Reduce model size further
- Try different input representations

"Not enough data" is NEVER a valid final conclusion. It's a problem statement.

## Evaluation

- Primary metric: val_sharpe (for model selection), test_sharpe (for final judgment)
- Benchmarks (for comparison only, NOT targets to beat): Equal Weight, MinVar, MLP
- A model with lower Sharpe than MinVar but valid attention-based regime detection is MORE valuable than MinVar — because it can improve with more data. MinVar cannot.
- Secondary: visualize attention weights across different market periods. Do they change? Do they make sense?

## Regime Detection Quality (must report)

Every attention experiment MUST include in its card:
- Attention weight visualization or summary statistics across 3+ distinct market periods
- Weight entropy: does it change over time? (static attention = not learning regimes)
- Portfolio composition shift: does allocation change meaningfully between calm and volatile periods?

## What NOT to Do
- No models >25K params
- No external macro data as input features
- No two-stage predict→optimize
- No categorical regime labels
- No declaring victory with non-attention models

## Key References
- iTransformer (ICLR 2024): variables-as-tokens = spatial attention
- PatchTST (ICLR 2023): patching time series for temporal attention
- Crossformer (ICLR 2023): two-stage cross-time/cross-variable
- Signature-Informed Transformer (2026): end-to-end CVaR, path signatures
- Portfolio Transformer (2022): direct allocation, 7 ETFs

## Data
- 17 ETFs × ~21yr daily
- Platform: Mac Mini M4, 32GB, MPS backend
