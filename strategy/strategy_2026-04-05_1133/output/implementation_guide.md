# Implementation Guide: Agent SDK While Loop

## Phase 1: Setup (5 minutes)

```bash
# 1. daemon 디렉토리 생성
mkdir -p /Users/ryan/.openclaw/workspace/asset_attention/daemon/prompts
mkdir -p /Users/ryan/.openclaw/workspace/asset_attention/loop_control

# 2. claude_agent_sdk 설치 확인
python3 -c "import claude_agent_sdk; print('SDK available')"

# 3. 권한 설정
touch /Users/ryan/.openclaw/workspace/asset_attention/loop_control/STOP
rm /Users/ryan/.openclaw/workspace/asset_attention/loop_control/STOP
```

## Phase 2: Core Files (20 minutes)

### File 1: safeguards.py

```python
#!/usr/bin/env python3
"""Safety controls for the autonomous loop."""

import json
import time
import psutil
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class CostTracker:
    """Track API costs per batch and total."""
    batch_cost: float = 0.0
    total_cost: float = 0.0
    batch_count: int = 0
    max_cost_per_batch: float = 20.0
    max_total_cost: float = 400.0
    
    def add_cost(self, amount: float):
        self.batch_cost += amount
        self.total_cost += amount
    
    def new_batch(self):
        self.batch_cost = 0.0
        self.batch_count += 1
    
    def check_limits(self) -> tuple[bool, Optional[str]]:
        if self.batch_cost > self.max_cost_per_batch:
            return False, f"Batch cost ${self.batch_cost:.2f} exceeds ${self.max_cost_per_batch}"
        if self.total_cost > self.max_total_cost:
            return False, f"Total cost ${self.total_cost:.2f} exceeds ${self.max_total_cost}"
        return True, None
    
    def save(self, path: Path):
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> 'CostTracker':
        if path.exists():
            with open(path) as f:
                return cls(**json.load(f))
        return cls()

class MemoryMonitor:
    """Monitor system memory and restart if needed."""
    
    def __init__(self, threshold_percent: float = 80.0):
        self.threshold = threshold_percent
    
    def check(self) -> tuple[bool, Optional[str]]:
        mem = psutil.virtual_memory()
        if mem.percent > self.threshold:
            return False, f"Memory at {mem.percent}% (threshold: {self.threshold}%)"
        return True, None

class StopSignal:
    """Check for human intervention signals."""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.stop_file = workspace / "loop_control" / "STOP"
        self.pause_file = workspace / "loop_control" / "PAUSE"
    
    def should_stop(self) -> bool:
        return self.stop_file.exists()
    
    def should_pause(self) -> bool:
        return self.pause_file.exists()
    
    def wait_if_paused(self):
        while self.should_pause() and not self.should_stop():
            time.sleep(10)
```

### File 2: main_daemon.py

```python
#!/usr/bin/env python3
"""
Asset Attention Autonomous Loop Daemon
Agent SDK While Loop implementation
"""

import sys
import json
import time
import signal
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from safeguards import CostTracker, MemoryMonitor, StopSignal

WORKSPACE = Path("/Users/ryan/.openclaw/workspace/asset_attention")
LOOP_CONTROL = WORKSPACE / "loop_control"
CARDS = WORKSPACE / "cards"

def load_prompt(name: str) -> str:
    """Load prompt from daemon/prompts/"""
    prompt_file = Path(__file__).parent / "prompts" / f"{name}.md"
    return prompt_file.read_text()

def spawn_explorer():
    """Run Explorer subagent for 5 experiments."""
    from claude_agent_sdk import spawn_subagent
    
    print(f"[{datetime.now()}] Spawning Explorer...")
    
    explorer = spawn_subagent(
        task=load_prompt("explorer_v2"),
        max_turns=100,  # 5 experiments × ~20 turns
        timeout_seconds=1800  # 30 min
    )
    
    try:
        result = explorer.run()
        print(f"[{datetime.now()}] Explorer completed: {result}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Explorer failed: {e}")
        return False

def spawn_critic():
    """Run Critic subagent for review."""
    from claude_agent_sdk import spawn_subagent
    
    print(f"[{datetime.now()}] Spawning Critic...")
    
    critic = spawn_subagent(
        task=load_prompt("critic_v2"),
        max_turns=50,
        timeout_seconds=600  # 10 min
    )
    
    try:
        verdict = critic.run()
        print(f"[{datetime.now()}] Critic verdict: {verdict}")
        return verdict
    except Exception as e:
        print(f"[{datetime.now()}] Critic failed: {e}")
        return "ERROR"

def check_needs_critic() -> bool:
    """Check if Critic review is pending."""
    return (WORKSPACE / "NEEDS_CRITIC").exists()

def save_checkpoint(batch_num: int, verdict: str):
    """Save loop state for resumption."""
    checkpoint = {
        "batch": batch_num,
        "verdict": verdict,
        "timestamp": datetime.now().isoformat(),
        "card_count": len(list(CARDS.glob("exp_*.json")))
    }
    
    checkpoint_file = LOOP_CONTROL / f"checkpoint_{batch_num:03d}.json"
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f, indent=2)
    
    # Also save as "latest" for easy access
    latest = LOOP_CONTROL / "checkpoint_latest.json"
    with open(latest, 'w') as f:
        json.dump(checkpoint, f, indent=2)

def main():
    """Main loop orchestrator."""
    print("=" * 60)
    print("Asset Attention Autonomous Loop")
    print("Agent SDK While Loop Implementation")
    print("=" * 60)
    
    # Initialize safeguards
    cost_tracker = CostTracker.load(LOOP_CONTROL / "cost_log.json")
    memory_monitor = MemoryMonitor(threshold_percent=80.0)
    stop_signal = StopSignal(WORKSPACE)
    
    batch_num = cost_tracker.batch_count
    
    print(f"[{datetime.now()}] Starting from batch {batch_num}")
    print(f"[{datetime.now()}] Total cost so far: ${cost_tracker.total_cost:.2f}")
    
    try:
        while True:
            # Check stop signal
            if stop_signal.should_stop():
                print(f"[{datetime.now()}] STOP signal detected. Exiting.")
                break
            
            if stop_signal.should_pause():
                print(f"[{datetime.now()}] PAUSE signal detected. Waiting...")
                stop_signal.wait_if_paused()
                continue
            
            # Check memory
            mem_ok, mem_msg = memory_monitor.check()
            if not mem_ok:
                print(f"[{datetime.now()}] Memory warning: {mem_msg}")
                print(f"[{datetime.now()}] Consider restarting daemon.")
            
            # Check cost limits
            cost_ok, cost_msg = cost_tracker.check_limits()
            if not cost_ok:
                print(f"[{datetime.now()}] Cost limit reached: {cost_msg}")
                break
            
            # Determine next action
            if check_needs_critic():
                # Critic phase
                verdict = spawn_critic()
                save_checkpoint(batch_num, verdict)
                
                if verdict == "FAIL":
                    print(f"[{datetime.now()}] FAIL verdict. Stopping for human review.")
                    break
                elif verdict == "REVISE":
                    print(f"[{datetime.now()}] REVISE verdict. Continuing with revisions.")
                else:  # PASS
                    batch_num += 1
                    cost_tracker.new_batch()
                    print(f"[{datetime.now()}] PASS verdict. Starting batch {batch_num}.")
            else:
                # Explorer phase
                success = spawn_explorer()
                if not success:
                    print(f"[{datetime.now()}] Explorer failed. Retrying in 60s...")
                    time.sleep(60)
                    continue
                
                # Explorer should have created NEEDS_CRITIC
                if not check_needs_critic():
                    print(f"[{datetime.now()}] Warning: Explorer didn't create NEEDS_CRITIC")
                    # Wait and check again
                    time.sleep(10)
            
            # Save state
            cost_tracker.save(LOOP_CONTROL / "cost_log.json")
            
            # Periodic restart every 5 batches
            if batch_num > 0 and batch_num % 5 == 0:
                print(f"[{datetime.now()}] Completed {batch_num} batches. Restarting daemon.")
                break
            
            # Small delay between iterations
            time.sleep(5)
    
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Interrupted by user.")
    except Exception as e:
        print(f"[{datetime.now()}] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        cost_tracker.save(LOOP_CONTROL / "cost_log.json")
        print(f"[{datetime.now()}] Daemon stopped. Total cost: ${cost_tracker.total_cost:.2f}")
        print(f"[{datetime.now()}] Run `python main_daemon.py` to resume.")

if __name__ == "__main__":
    main()
```

## Phase 3: Prompts (15 minutes)

See `prompts/explorer_v2.md` and `prompts/critic_v2.md` for the full prompt content.
Key changes from v1:
- Clearer exit protocol
- Explicit git commands
- Cost awareness
- Better error handling instructions

## Phase 4: First Run (10 minutes)

```bash
# 1. Navigate to daemon directory
cd /Users/ryan/.openclaw/workspace/asset_attention/daemon

# 2. Test run (dry-run mode, or with limits)
python main_daemon.py

# 3. In another terminal, monitor
watch -n 5 'cat ../loop_control/checkpoint_latest.json'

# 4. To stop
touch /Users/ryan/.openclaw/workspace/asset_attention/loop_control/STOP
```

## Troubleshooting

### Problem: "claude_agent_sdk not found"
**Fix:** SDK는 Claude Code 내부에서만 사용 가능. 외부 Python에서는 직접 호출 불가.
**Solution:** `main_daemon.py`를 Claude Code 환경에서 실행하거나, subprocess로 `claude -p` 호출.

**Revised approach:**
```python
# Instead of importing SDK, use subprocess
import subprocess

def spawn_explorer():
    result = subprocess.run(
        ["claude", "-p", load_prompt("explorer_v2"), 
         "--allowed-tools", "Bash,Read,Write,Edit"],
        capture_output=True,
        text=True,
        timeout=1800
    )
    return result.returncode == 0
```

### Problem: Explorer hangs
**Fix:** Add timeout in subprocess call
```python
subprocess.run(..., timeout=1800)  # 30 min max
```

### Problem: Cost exceeds limit mid-batch
**Fix:** Batch 내에서도 중간 체크
```python
# Explorer should periodically report cost
# Daemon kills if approaching limit
```

## Success Criteria

- [ ] 5 experiments complete without manual intervention
- [ ] Critic review automatically triggered
- [ ] Verdict (PASS/REVISE/FAIL) correctly handled
- [ ] Cost tracked accurately
- [ ] STOP signal works immediately
- [ ] Can resume after restart
- [ ] No data loss on crash
