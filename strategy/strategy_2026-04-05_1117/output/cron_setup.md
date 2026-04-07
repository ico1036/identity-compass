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
