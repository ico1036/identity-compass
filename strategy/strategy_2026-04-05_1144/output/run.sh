#!/bin/bash
# run.sh - Start Asset Attention Ralph Loop

cd /Users/ryan/.openclaw/workspace/asset_attention

echo "====================================="
echo "Asset Attention Autonomous Loop"
echo "Powered by Ralph"
echo "====================================="
echo ""

# Check for STOP file and remove if exists (clean start)
if [ -f "STOP" ]; then
    echo "Removing existing STOP file..."
    rm -f STOP
fi

# Check Ralph installation
if ! python3 -c "import ralph" 2>/dev/null; then
    echo "❌ Ralph not installed"
    echo "Install: pip install ralph-loop"
    exit 1
fi

echo "✓ Ralph found"
echo ""

# Check workspace
if [ ! -f "train.py" ]; then
    echo "❌ Not in asset_attention directory"
    exit 1
fi

echo "✓ Workspace verified"
echo ""

# Start Ralph loop
echo "Starting Ralph loop..."
echo "Create STOP file to stop gracefully"
echo ""

python3 ralph_plugin.py

echo ""
echo "Loop ended. Check docs/reviews/ for latest verdict."
