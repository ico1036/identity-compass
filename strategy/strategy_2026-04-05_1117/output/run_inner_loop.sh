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
