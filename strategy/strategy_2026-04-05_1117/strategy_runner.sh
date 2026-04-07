#!/bin/bash
# strategy_runner.sh - Claude Code를 headless로 실행

cd /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1117

echo "전략팀 작업 시작..."
echo "참고 파일 읽는 중..."

# 간단한 프롬프트로 테스트
cat << 'INNER_SCRIPT' > /tmp/run_strategy.sh
#!/bin/bash
echo "=== Claude Code Strategy Team ==="
echo "Reading brief..."
cat brief/brief.md | head -20
echo ""
echo "Reading context files..."
ls -la context/
echo ""
echo "Creating output files..."

# 1. run_inner_loop.sh
cat << 'EOF' > output/run_inner_loop.sh
#!/bin/bash
# Inner Loop Orchestrator - Claude Code Headless Version

WORKSPACE="/Users/ryan/.openclaw/workspace/asset_attention"
LOCK_FILE="$WORKSPACE/LOCK"
NEEDS_CRITIC="$WORKSPACE/NEEDS_CRITIC"
STALE_THRESHOLD=21600  # 6 hours in seconds

echo "[$(date)] Checking inner loop state..."

# Check if LOCK exists and is stale
if [ -f "$LOCK_FILE" ]; then
    LOCK_AGE=$(($(date +%s) - $(stat -f %m "$LOCK_FILE")))
    if [ $LOCK_AGE -gt $STALE_THRESHOLD ]; then
        echo "[$(date)] Stale LOCK detected ($LOCK_AGE seconds). Removing..."
        rm -f "$LOCK_FILE"
    else
        echo "[$(date)] Active LOCK detected ($LOCK_AGE seconds). Skipping."
        exit 0
    fi
fi

# Determine role based on state files
if [ -f "$NEEDS_CRITIC" ]; then
    echo "[$(date)] Critic review needed."
    ROLE="critic"
else
    echo "[$(date)] Explorer run needed."
    ROLE="explorer"
fi

# Create LOCK
echo "$(date)" > "$LOCK_FILE"

# Run appropriate task via Claude Code
if [ "$ROLE" = "critic" ]; then
    echo "[$(date)] Running Critic..."
    claude -p "$(cat /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1117/output/critic_task.md)" \
        --allowed-tools "Bash,Read,Write,Edit" \
        --dangerously-skip-permissions
    rm -f "$NEEDS_CRITIC"
else
    echo "[$(date)] Running Explorer..."
    claude -p "$(cat /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1117/output/explorer_task.md)" \
        --allowed-tools "Bash,Read,Write,Edit" \
        --dangerously-skip-permissions
fi

# Cleanup
rm -f "$LOCK_FILE"
echo "[$(date)] Inner loop cycle complete."
EOF
chmod +x output/run_inner_loop.sh

# 2. explorer_task.md
cat << 'EOF' > output/explorer_task.md
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
EOF

# 3. critic_task.md
cat << 'EOF' > output/critic_task.md
# Critic Task

You are the Critic agent (Quant CIO) for asset_attention.

## Setup
1. cd /Users/ryan/.openclaw/workspace/asset_attention
2. Read docs/critic.md for persona
3. Read docs/philosophy.md for THE MISSION
4. Read latest 5 experiment cards from cards/
5. Read current train.py

## Review Process
1. What does the model learn? (one sentence)
2. Walk through data journey
3. How many independent data points?
4. Do numbers make sense?
5. Would you put money in this?
6. Does attention show regime signal?
7. Compare to EW and static benchmarks

## Output
Write review to docs/reviews/review_r7_XX.md following format in docs/critic.md

Verdict: PASS / REVISE / FAIL

## Exit Protocol
1. Write review
2. Update docs/insights.md if REVISE/FAIL
3. git add -A && git commit && git push
4. Remove NEEDS_CRITIC
5. Remove LOCK
6. EXIT
EOF

# 4. cron_setup.md
cat << 'EOF' > output/cron_setup.md
# Cron Setup Guide for Mac Mini

## 1. Edit crontab
```bash
crontab -e
```

## 2. Add entry (runs every 15 minutes)
```
*/15 * * * * /bin/bash /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1117/output/run_inner_loop.sh >> /tmp/inner_loop.log 2>&1
```

## 3. Grant permissions (first time only)
```bash
# Allow cron to access Desktop/Documents folders
# System Preferences > Security & Privacy > Privacy > Full Disk Access
# Add /usr/sbin/cron
```

## 4. Test manually first
```bash
/Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1117/output/run_inner_loop.sh
```

## 5. Monitor logs
```bash
tail -f /tmp/inner_loop.log
```

## Alternative: launchd (more reliable on macOS)
See output/com.innerloop.runner.plist for launchd config.
EOF

echo "Output files created successfully!"
ls -la output/
INNER_SCRIPT

bash /tmp/run_strategy.sh
