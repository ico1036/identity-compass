# Monitoring Setup

## Human Interface Design

### Control Files

All control files in `/Users/ryan/.openclaw/workspace/asset_attention/loop_control/`:

| File | Purpose | How to Use |
|------|---------|------------|
| `STOP` | Graceful stop | `touch STOP` - stops after current batch |
| `PAUSE` | Pause loop | `touch PAUSE` - waits until removed |
| `EMERGENCY_STOP` | Immediate kill | `touch EMERGENCY_STOP` - kills daemon now |

### Status Files

| File | Content | Update Frequency |
|------|---------|-----------------|
| `checkpoint_latest.json` | Current batch, verdict, timestamp | Every batch |
| `cost_log.json` | Running cost totals | Every batch |
| `daemon.log` | Full execution log | Real-time |

### Quick Status Check

```bash
# One-liner status
alias astatus='cat /Users/ryan/.openclaw/workspace/asset_attention/loop_control/checkpoint_latest.json | python3 -m json.tool'

# Cost check
alias acost='cat /Users/ryan/.openclaw/workspace/asset_attention/loop_control/cost_log.json | python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"Total: ${d[\"total_cost\"]:.2f}, Batch: {d[\"batch_count\"]}\")"'

# Stop loop
alias astop='touch /Users/ryan/.openclaw/workspace/asset_attention/loop_control/STOP'

# Resume
alias aresume='rm -f /Users/ryan/.openclaw/workspace/asset_attention/loop_control/STOP && cd /Users/ryan/.openclaw/workspace/asset_attention/daemon && python main_daemon.py'
```

## Optional: Telegram Notifications

```python
# telegram_notify.py (optional add-on)
import os
import requests

def notify_batch_complete(batch_num: int, verdict: str, cost: float):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    message = f"""
🤖 *Asset Attention Loop Update*

Batch {batch_num} complete
Verdict: {verdict}
Cost this batch: ${cost:.2f}

Use `/status` for details
    """
    
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
    )
```

## Optional: launchd Watchdog (Mac)

```xml
<!-- com.assetattention.daemon.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.assetattention.daemon</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/python3</string>
        <string>/Users/ryan/.openclaw/workspace/asset_attention/daemon/main_daemon.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/ryan/.openclaw/workspace/asset_attention</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/tmp/assetattention.out</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/assetattention.err</string>
</dict>
</plist>
```

**Install:**
```bash
cp com.assetattention.daemon.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.assetattention.daemon.plist
launchctl start com.assetattention.daemon
```

## Minimal Monitoring (Recommended)

No watchdog, no Telegram. Just:

1. `checkpoint_latest.json` - check anytime
2. `STOP` file - stop when needed
3. Check logs with `tail -f` occasionally

Simple, reliable, sufficient for thesis work.
