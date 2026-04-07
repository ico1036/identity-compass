# Ralph Plugin Setup Guide

## Prerequisites

- Python 3.11+
- Ralph installed: `pip install ralph-loop`
- Claude Code CLI installed
- asset_attention repository cloned

## Installation

### 1. Copy Plugin Files

```bash
cd /Users/ryan/.openclaw/workspace/asset_attention

# Copy plugin
cp /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1144/output/ralph_plugin.py .

# Copy prompts
mkdir -p ralph_prompts
cp /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1144/output/prompts/*.md ralph_prompts/

# Copy run script
cp /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1144/output/run.sh .
chmod +x run.sh
```

### 2. Verify Structure

```
asset_attention/
├── ralph_plugin.py          # ← new
├── ralph_prompts/
│   ├── explorer_v2.md       # ← new
│   └── critic_v2.md         # ← new
├── run.sh                   # ← new
├── train.py                 # existing
├── docs/                    # existing
├── cards/                   # existing
└── ...
```

### 3. Test Run

```bash
./run.sh
```

Expected output:
```
=====================================
Asset Attention Autonomous Loop
Powered by Ralph
=====================================

✓ Ralph found
✓ Workspace verified

Starting Ralph loop...
Create STOP file to stop gracefully

[Ralph] Starting Explorer phase...
...
```

## Usage

### Start Loop

```bash
./run.sh
```

### Stop Loop

```bash
# Graceful stop (after current batch)
touch STOP

# Or Ctrl+C (immediate)
```

### Check Status

```bash
# Latest review
cat docs/reviews/review_r7_*.md | tail -50

# Experiment count
ls cards/exp_*.json | wc -l

# Current checkpoint
cat docs/insights.md | tail -30
```

## Troubleshooting

### "Ralph not found"

```bash
pip install ralph-loop
# or
pip install /path/to/ralph  # if local
```

### "STOP file exists"

```bash
rm -f STOP
./run.sh
```

### Ralph API changes

If Ralph's API changes, update `ralph_plugin.py`:

```python
# Check Ralph docs for latest API
from ralph import Loop, StopHook  # may change
```

## How It Works

1. **Ralph loads** `ralph_plugin.py`
2. **AssetAttentionLoop** initializes Explorer and Critic
3. **Explorer** runs 5 experiments → creates NEEDS_CRITIC
4. **Critic** reviews → writes verdict → removes NEEDS_CRITIC
5. **Verdict**: PASS → next batch, REVISE → retry, FAIL → stop
6. **StopHook** checks STOP file every iteration

## Customization

### Change batch size

Edit `ralph_plugin.py`:
```python
self.explorer = Explorer(
    prompt_file=...,
    max_experiments=3,  # change from 5
)
```

### Add custom stop condition

Edit `check_stop()` in `ralph_plugin.py`:
```python
def check_stop(self) -> StopHook:
    if (WORKSPACE / "STOP").exists():
        return StopHook.INTERRUPT
    if (WORKSPACE / "PAUSE").exists():
        return StopHook.PAUSE
    return StopHook.CONTINUE
```

## Migration from Old System

Old: cron + OpenClaw
New: Ralph plugin

1. Disable old cron: `crontab -e` → remove asset_attention entry
2. Install Ralph plugin (this guide)
3. Run: `./run.sh`

Done. Simpler, more reliable.
