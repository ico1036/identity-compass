# Architecture Comparison: Ralph Plugin vs Agent SDK While Loop

## Executive Summary

| Dimension | Ralph Loop Plugin | Agent SDK While Loop |
|-----------|-------------------|---------------------|
| **Complexity** | Medium (external dependency) | Low (self-contained) |
| **Flexibility** | Limited by Ralph's design | High (full control) |
| **Monitoring** | Built-in cost tracking | Needs custom implementation |
| **Recovery** | Ralph handles restarts | Needs watchdog (minimal cron) |
| **Context Sharing** | Limited between batches | Rich within single session |
| **Learning Curve** | Must learn Ralph patterns | Just SDK documentation |
| **Integration Risk** | Ralph designed for Helix | Purpose-built for asset_attention |

## Detailed Analysis

### A. Ralph Loop Plugin Approach

**What is Ralph Loop?**
- Multi-agent framework designed for quantitative strategy generation
- Built-in cost tracking, budget caps, feature gates
- Fork-based subagent spawning
- 3-scope memory (local, session, global)

**Pros:**
1. **Proven infrastructure** - Already handles edge cases
2. **Cost controls** - Budget cap enforcement, spending tracking
3. **Standardized patterns** - Consistent agent behavior
4. **Built-in review gates** - Quality checkpoints

**Cons:**
1. **Over-engineering risk** - Ralph designed for 1000 alphas/day scale
2. **Tight coupling** - Asset_attention becomes dependent on Helix infrastructure
3. **Learning overhead** - Must understand Ralph's abstractions
4. **Customization limits** - Plugin architecture constrains modifications
5. **Context loss** - Each batch starts fresh (no memory between Ralph runs)

**Best for:** Large-scale production systems with multiple strategies

### B. Agent SDK While Loop Approach

**Concept:**
```python
# main_daemon.py
from claude_agent_sdk import spawn_subagent
import signal

running = True

def stop_handler(signum, frame):
    global running
    running = False
    Path("STOP").touch()

signal.signal(signal.SIGTERM, stop_handler)

while running and not Path("STOP").exists():
    # Explorer phase
    explorer = spawn_subagent(
        task=load_prompt("explorer_v2"),
        max_turns=50
    )
    results = explorer.run()
    
    if Path("STOP").exists():
        break
    
    # Critic phase  
    critic = spawn_subagent(
        task=load_prompt("critic_v2"),
        max_turns=30
    )
    verdict = critic.review(results)
    
    if verdict == "FAIL":
        notify_human("Mission requires intervention")
        break
    elif verdict == "REVISE":
        continue
    # PASS: continue to next batch
```

**Pros:**
1. **Simplicity** - Pure Python, no external framework
2. **Full control** - Every aspect customizable
3. **Context preservation** - Single session, shared state
4. **Transparent** - Easy to debug and modify
5. **Purpose-built** - Exactly matches asset_attention needs

**Cons:**
1. **Memory pressure** - Long-running session (mitigation: restart every N batches)
2. **Cost accumulation** - Continuous billing (mitigation: batch size limits)
3. **No built-in safeguards** - Must implement cost tracking
4. **Recovery complexity** - Needs watchdog for crashes

**Mitigations for Cons:**

```python
# Built-in safeguards
class MonitoredLoop:
    def __init__(self, max_cost=10.0, max_batches=20):
        self.cost_tracker = CostTracker()
        self.batch_count = 0
        self.max_cost = max_cost
        self.max_batches = max_batches
    
    def should_continue(self):
        if self.cost_tracker.total > self.max_cost:
            notify_human(f"Cost limit ${self.max_cost} reached")
            return False
        if self.batch_count >= self.max_batches:
            notify_human(f"Max {self.max_batches} batches completed")
            return False
        if Path("STOP").exists():
            return False
        return True
    
    def run(self):
        while self.should_continue():
            self.run_batch()
            self.batch_count += 1
            # Periodic restart to manage memory
            if self.batch_count % 5 == 0:
                self.checkpoint_and_restart()
```

## Recommendation: Agent SDK While Loop

**Rationale:**

1. **Scale mismatch** - Ralph is designed for 1000 alphas/day industrial scale. Asset_attention needs ~50 experiments for thesis validation.

2. **Mission specificity** - Ralph's generic abstractions add complexity without benefit. Direct SDK gives precise control.

3. **Debugging simplicity** - When attention models fail (as they currently do), simple code is easier to diagnose than framework code.

4. **Educational value** - Understanding the loop mechanics directly informs experimental design choices.

5. **Migration path** - Can always migrate to Ralph later if scale demands it. The reverse is harder.

## Hybrid Compromise

If Ralph infrastructure is already available and familiar:

```python
# ralph_wrapper.py
# Use Ralph for cost tracking and monitoring
# But keep the loop simple

from ralph import CostTracker, BudgetCap
from claude_agent_sdk import spawn_subagent

@BudgetCap(max_cost=20.0)
@CostTracker
class AssetAttentionLoop:
    def run(self):
        while not self.should_stop():
            with self.batch_scope():
                explorer = spawn_subagent(...)
                # ...
```

**Verdict:** Agent SDK While Loop as primary, Ralph components as optional addons for cost tracking only.
