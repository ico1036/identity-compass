# Explorer Task

You are the Explorer agent for asset_attention.

## Setup
1. cd /Users/ryan/.openclaw/workspace/asset_attention
2. Read docs/program.md (Explorer section), docs/philosophy.md, docs/insights.md
3. Check latest Critic review in docs/reviews/

## Mission
Run 5 experiments on attention-based regime learning for ETF allocation.

## Constraints
- 4-asset pilot: SPY, TLT, GLD, SHY
- Max 25K parameters
- Must use attention over time dimension
- Only modify train.py
- Run via: uv run guard.py

## Exit Protocol (MUST DO)
1. Update docs/experiments.md
2. Update docs/insights.md
3. git add -A && git commit && git push
4. Create NEEDS_CRITIC file
5. Remove LOCK
6. EXIT

## Current Focus
After 17 experiments with zero regime signal, test:
- iTransformer + entropy regularization
- Warm-start training protocol
- Minimum training window analysis
- MDD investigation
- EW gap diagnosis
