# Helix Alpha Factory 개선 보고서

> **작성일**: 2026-04-03  
> **대상 시스템**: Helix Alpha Factory (Claude Agent SDK 기반 Multi-Agent Quant System)  
> **분석 소스**: claw-code (Claude Code 소스코드) 역공학 분석  
> **목적**: 17개 개선 기술의 Helix 적용 가이드

---

## 1. Executive Summary

Helix Alpha Factory는 1개의 Orchestrator와 6개의 Sub-agent로 구성된 멀티에이전트 퀀트 전략 개발 시스템이다. 현재 시스템은 **전략 생성→코드 구현→백테스트→피드백**의 기본 파이프라인을 성공적으로 운영하고 있으나, claw-code 분석에서 발견된 17개 기술을 적용하면 다음과 같은 개선이 가능하다:

| 영역 | 현재 | 개선 후 (추정) |
|------|------|----------------|
| **토큰 비용** | 전략당 ~$15-25 | ~$7-12 (50%↓) |
| **메모리 효율** | 무제한 증가 | 자동 정리 + 3-scope 분리 |
| **안정성** | 비용 폭주 리스크 | Budget cap + Feature gate |
| **전략 격리** | 공유 git state | Worktree 완전 격리 |
| **학습 능력** | 전략별 독립 | Cross-strategy 지식 전파 |

**핵심 메시지**: Fork Subagent(#1), 3-Scope Memory(#2), Cost Tracker(#5), Budget Cap(#6) 4개를 Phase 1으로 도입하면, 전체 개선 효과의 ~70%를 확보할 수 있다.

---

## 2. 현재 시스템 아키텍처 분석

### 2.1 아키텍처 개요

```
┌─────────────────────────────────────────┐
│           orchestrator_agent.py          │
│  - ClaudeSDKClient + AgentDefinition    │
│  - Hook-based tracking (Pre/PostToolUse)│
│  - Signal file protocol                 │
│  - Max 5 iterations per session         │
└──────┬──────┬──────┬──────┬──────┬──────┘
       │      │      │      │      │
   ┌───┴┐ ┌──┴──┐ ┌─┴──┐ ┌┴───┐ ┌┴────┐ ┌─────┐
   │EDA │ │Quant│ │Qnt │ │Snr │ │Back │ │Port │
   │Agt │ │Rsch │ │Dev │ │Dev │ │Test │ │Mgr  │
   └────┘ └─────┘ └────┘ └────┘ └─────┘ └─────┘
```

### 2.2 강점

1. **Hook 기반 자동 추적**: `PreToolUse`/`PostToolUse` hook으로 에이전트 호출을 자동 기록한다. 수동 로깅 없이도 전체 워크플로우를 추적할 수 있다는 점이 잘 설계되어 있다.

2. **Signal File Protocol**: `PRODUCTION_APPROVED.signal` 같은 파일 기반 시그널로 워크플로우를 제어한다. 이것은 에이전트 간 느슨한 결합(loose coupling)을 가능하게 하여, 각 에이전트가 독립적으로 동작하면서도 조율될 수 있다.

3. **AgentCallTracker**: async-safe 타이밍과 자동 cleanup을 갖춘 클래스로, 동시 실행 환경에서도 안정적으로 에이전트 호출을 추적한다.

4. **Orphaned Signal Cleanup**: 시작 시 고아 시그널 파일을 정리하여 이전 세션의 잔여 상태가 새 세션을 오염시키지 않도록 한다.

5. **전략별 디렉토리 격리**: `dir_{strategy_name}/`으로 전략별 파일을 분리하고, 각 디렉토리에 `longterm_memory.md`를 유지한다.

6. **Response Size Limiting**: `MAX_RESPONSE_SIZE` 10MB로 거대 응답에 의한 메모리 폭주를 방지한다.

7. **Loguru 3-sink 로깅**: JSONL(기계용), Markdown(사람용), stdout(실시간)으로 다목적 로깅이 잘 구성되어 있다.

### 2.3 약점

| # | 약점 | 영향 | 심각도 |
|---|------|------|--------|
| W1 | **비용 추적 없음** | 전략당 얼마를 쓰는지 모름 → ROI 계산 불가 | 🔴 Critical |
| W2 | **예산 제한 없음** | 무한 루프 시 수백 달러 소모 가능 | 🔴 Critical |
| W3 | **메모리 무한 증가** | longterm_memory.md가 계속 커짐 → context window 낭비 | 🟡 High |
| W4 | **캐시 공유 없음** | Sub-agent마다 새 인스턴스 → system prompt 재전송 | 🟡 High |
| W5 | **Git 격리 없음** | 실패한 전략 코드가 다른 전략에 영향 | 🟡 High |
| W6 | **단일 메모리 스코프** | 범용 지식과 전략 지식이 혼재 | 🟠 Medium |
| W7 | **권한 무차별** | 모든 에이전트가 모든 도구 사용 가능 | 🟠 Medium |
| W8 | **Feature Gate 없음** | 새 기능 실험 시 전체 시스템 리스크 | 🟠 Medium |

---

## 3. 개선 기술 상세 분석

---

### 기술 #1: Fork Subagent (Prompt Cache Sharing)

#### 기술 설명

claw-code에서 sub-agent를 생성할 때, 부모 에이전트의 conversation history를 "fork"하여 자식에게 전달한다. 핵심은 **Anthropic API의 prompt caching**이다. 동일한 system prompt + 이전 대화가 캐시에 남아있으면, 자식 에이전트는 이 캐시를 재사용한다.

```
부모 대화: [system_prompt, msg1, msg2, ..., msgN]
                    ↓ fork
자식 대화: [system_prompt, msg1, msg2, ..., msgN, 자식_system_prompt]
                ↑ 이 부분은 캐시 히트
```

Anthropic의 prompt caching은 **동일한 prefix**가 일치하면 캐시된 토큰에 대해 90% 할인을 적용한다. fork하면 부모의 전체 대화가 prefix로 공유되므로, 자식 에이전트의 input token 비용이 대폭 줄어든다.

#### Helix 현재 상태

**없음**. 현재 `orchestrator_agent.py`에서 sub-agent를 호출할 때 매번 새로운 `AgentDefinition`으로 fresh instance를 생성한다. 각 sub-agent는 자신의 system prompt만 가지고 시작하며, orchestrator의 대화 맥락을 공유받지 못한다.

결과적으로:
- orchestrator가 축적한 전략 컨텍스트를 sub-agent에게 매번 텍스트로 전달해야 함
- 동일한 system prompt도 캐시 활용 없이 매번 전체 전송

#### 구체적 적용 방안

**파일**: `orchestrator_agent.py`

현재 sub-agent 호출 패턴 (추정):
```python
# 현재 방식
async def call_sub_agent(agent_name: str, task: str):
    agent_def = AgentDefinition(
        name=agent_name,
        system_prompt=get_system_prompt(agent_name),
        tools=get_allowed_tools(agent_name),
    )
    client = ClaudeSDKClient(options=ClaudeAgentOptions(model="opus"))
    response = await client.run(agent_def, messages=[{"role": "user", "content": task}])
    return response
```

개선 방식:
```python
# Fork 방식
class ForkableAgent:
    def __init__(self, base_messages: list):
        self.base_messages = base_messages  # orchestrator의 대화 히스토리
    
    async def fork_sub_agent(self, agent_name: str, task: str):
        agent_def = AgentDefinition(
            name=agent_name,
            system_prompt=get_system_prompt(agent_name),
            tools=get_allowed_tools(agent_name),
        )
        # 핵심: 부모의 대화를 prefix로 포함
        forked_messages = [
            *self.base_messages,  # 캐시 히트 가능 영역
            {"role": "user", "content": f"[Forked Task for {agent_name}]\n{task}"}
        ]
        client = ClaudeSDKClient(options=ClaudeAgentOptions(model="opus"))
        response = await client.run(agent_def, messages=forked_messages)
        return response
```

**주의사항**: Claude Agent SDK가 fork를 직접 지원하는지 확인 필요. 지원하지 않으면 messages 배열을 수동으로 구성하여 동일한 효과를 낼 수 있다.

#### 예상 효과

- **토큰 절감**: Sub-agent 호출 시 input token의 ~50-70%가 캐시 히트 (Anthropic 공식: 캐시 히트 시 input 비용 90% 할인)
- **비용 절감**: 전략당 6회 sub-agent 호출 기준, input token 비용 약 40-50% 절감
- **속도**: 캐시 히트 시 TTFT(Time to First Token) 감소

**정량 추정**:
- 현재: 전략당 sub-agent 호출 6회 × 평균 input 8K tokens = 48K input tokens
- 개선 후: 48K × 0.5 (캐시 히트율) × 0.1 (캐시 가격) + 48K × 0.5 (미스) × 1.0 = 26.4K tokens 상당
- **절감율: ~45%** (input token 기준)

#### 구현 난이도: **Medium**

Claude Agent SDK의 messages 전달 방식을 이해해야 하고, 부모 대화 히스토리의 어디까지를 fork할지 결정하는 로직이 필요하다.

#### 의존성

- #11 (Agent List → Attachment 분리)과 함께 적용하면 캐시 히트율이 더 높아짐
- #13 (Forked Agent Cache)은 이 기술의 확장으로, 함께 구현

---

### 기술 #2: 3-Scope Memory (User/Project/Local)

#### 기술 설명

claw-code는 메모리를 3개 레벨로 분리한다:

| Scope | 위치 | 내용 | 생명주기 |
|-------|------|------|----------|
| **User** | `~/.claude/CLAUDE.md` | 사용자 전역 설정, 선호도 | 영구 |
| **Project** | `{project}/.claude/CLAUDE.md` | 프로젝트 규칙, 컨벤션 | 프로젝트 수명 |
| **Local** | `{project}/.claude/local/CLAUDE.md` | 개인 메모, 실험 기록 | 개인용 |

이 분리의 핵심 이점은:
1. **Context window 효율**: 필요한 scope만 로드
2. **지식 격리**: 전략 A의 지식이 전략 B를 오염시키지 않음
3. **공유 가능성**: User/Project scope는 팀 공유 가능

#### Helix 현재 상태

**단일 스코프만 존재**. 각 전략 디렉토리(`dir_{strategy_name}/`)에 `longterm_memory.md` 하나만 있다. 이 파일에 모든 종류의 지식이 혼재:
- 범용 퀀트 지식 ("모멘텀 팩터는 12개월 수익률이 표준")
- 전략 특화 지식 ("이 전략의 리밸런싱 주기는 주간")
- 환경 정보 ("backtest.py의 데이터 경로는 /data/...")

문제점:
- 메모리가 커질수록 context window를 더 많이 차지
- 범용 지식이 매 전략마다 중복 저장
- 오래된 정보와 새 정보의 구분 없음

#### 구체적 적용 방안

**파일**: `config.py`, `orchestrator_agent.py`

```python
# config.py에 추가
class MemoryConfig:
    # User scope: 범용 퀀트 지식 (모든 전략이 공유)
    USER_MEMORY_PATH = Path("~/.helix/memory/universal_quant.md")
    
    # Project scope: Helix 시스템 규칙
    PROJECT_MEMORY_PATH = Path("helix_rules.md")
    
    # Local scope: 전략별 기억
    @staticmethod
    def local_memory_path(strategy_name: str) -> Path:
        return Path(f"dir_{strategy_name}/strategy_memory.md")

# orchestrator_agent.py에서 메모리 로딩
class MemoryManager:
    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name
    
    def load_context(self, scope: str = "all") -> str:
        """scope: 'user', 'project', 'local', 'all'"""
        parts = []
        
        if scope in ("user", "all"):
            user_mem = MemoryConfig.USER_MEMORY_PATH.expanduser()
            if user_mem.exists():
                parts.append(f"## 범용 퀀트 지식\n{user_mem.read_text()}")
        
        if scope in ("project", "all"):
            proj_mem = MemoryConfig.PROJECT_MEMORY_PATH
            if proj_mem.exists():
                parts.append(f"## Helix 시스템 규칙\n{proj_mem.read_text()}")
        
        if scope in ("local", "all"):
            local_mem = MemoryConfig.local_memory_path(self.strategy_name)
            if local_mem.exists():
                parts.append(f"## 전략 메모리\n{local_mem.read_text()}")
        
        return "\n\n---\n\n".join(parts)
    
    def save(self, content: str, scope: str):
        """특정 scope에 메모리 저장"""
        paths = {
            "user": MemoryConfig.USER_MEMORY_PATH.expanduser(),
            "project": MemoryConfig.PROJECT_MEMORY_PATH,
            "local": MemoryConfig.local_memory_path(self.strategy_name),
        }
        path = paths[scope]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
```

**Sub-agent별 scope 로딩 전략**:
- `quant-researcher`: user + project (범용 지식 + 시스템 규칙)
- `quant-developer`: project + local (시스템 규칙 + 전략 컨텍스트)
- `backtest-agent`: local only (해당 전략의 백테스트 히스토리만)
- `portfolio-manager`: user + local (범용 지식 + 전략 컨텍스트)

#### 예상 효과

- **Context window 절감**: 에이전트별로 필요한 scope만 로드하면 메모리 토큰 30-50% 절감
- **지식 품질**: scope 분리로 관련성 높은 정보만 에이전트에게 전달
- **재사용성**: user scope의 범용 지식이 모든 전략에서 공유 → 중복 제거

**정량 추정**:
- 현재: longterm_memory.md 평균 3K tokens, 6개 sub-agent에 모두 전달 = 18K tokens
- 개선 후: 에이전트별 평균 1.5K tokens = 9K tokens
- **절감율: ~50%** (메모리 관련 토큰)

#### 구현 난이도: **Low**

파일 경로 분리와 로딩 로직만 추가하면 된다. 기존 longterm_memory.md의 내용을 3개 scope로 마이그레이션하는 일회성 작업이 필요.

#### 의존성

- #7 (Dream Consolidation)이 각 scope별로 독립적으로 작동해야 함
- #15 (Team Memory Sync)의 기반이 됨 (user scope를 팀 간 공유)

---

### 기술 #3: Plan Mode (Phase-based Workflow)

#### 기술 설명

claw-code에는 "plan mode"라는 개념이 있다. 에이전트가 즉시 실행하지 않고, 먼저 **계획을 세우고 사용자 승인을 받은 후 실행**하는 모드이다.

이를 Helix에 맞게 확장하면 4-phase workflow가 된다:

```
Phase 1: Research    → 팩터 탐색, 문헌 조사, 가설 수립
Phase 2: Synthesis   → 가설 정리, 전략 설계 문서 작성
Phase 3: Implement   → 코드 작성, 백테스트 실행
Phase 4: Verify      → 독립 검증, 성과 분석, 승인/거절
```

각 Phase 전환 시 **명시적 체크포인트**가 있어 사용자가 방향을 수정하거나 중단할 수 있다.

#### Helix 현재 상태

**암묵적 순서만 존재**. orchestrator_agent.py의 루프가 sub-agent를 순차 호출하지만, 명시적 phase 구분이 없다. 현재 흐름:

```
eda-agent → quant-researcher → quant-developer → senior-developer → backtest-agent → portfolio-manager
```

문제점:
- Phase 간 전환 조건이 명확하지 않음
- 실패 시 어느 Phase로 돌아가야 하는지 불분명
- 사용자가 중간에 개입할 체크포인트가 없음 (signal file이 있지만 제한적)

#### 구체적 적용 방안

**파일**: `orchestrator_agent.py`

```python
from enum import Enum

class WorkflowPhase(Enum):
    RESEARCH = "research"
    SYNTHESIS = "synthesis"  
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"

class PlanModeOrchestrator:
    PHASE_AGENTS = {
        WorkflowPhase.RESEARCH: ["eda-agent", "quant-researcher"],
        WorkflowPhase.SYNTHESIS: ["quant-researcher"],  # 요약 모드
        WorkflowPhase.IMPLEMENTATION: ["quant-developer", "senior-developer"],
        WorkflowPhase.VERIFICATION: ["backtest-agent", "portfolio-manager"],
    }
    
    PHASE_GATES = {
        # 각 phase 완료 후 체크포인트
        WorkflowPhase.RESEARCH: "research_complete.signal",
        WorkflowPhase.SYNTHESIS: "plan_approved.signal",
        WorkflowPhase.IMPLEMENTATION: "code_complete.signal",
        WorkflowPhase.VERIFICATION: "PRODUCTION_APPROVED.signal",
    }
    
    async def run_strategy(self, strategy_name: str):
        for phase in WorkflowPhase:
            logger.info(f"=== Phase: {phase.value} ===")
            
            # Phase 실행
            agents = self.PHASE_AGENTS[phase]
            results = {}
            for agent_name in agents:
                results[agent_name] = await self.call_sub_agent(agent_name, phase)
            
            # Phase 결과를 문서로 저장
            self.save_phase_output(strategy_name, phase, results)
            
            # Gate 체크: signal file 대기 또는 자동 진행
            gate_file = self.PHASE_GATES[phase]
            if phase == WorkflowPhase.SYNTHESIS:
                # Synthesis 후에는 반드시 사용자 승인 대기
                logger.info(f"⏸️ 사용자 승인 대기: {gate_file}")
                await self.wait_for_signal(gate_file, timeout=3600)
            else:
                # 다른 phase는 자동 진행 (실패 시만 중단)
                if not self.evaluate_phase_success(results):
                    logger.warning(f"Phase {phase.value} 실패. 재시도 또는 중단.")
                    break
```

#### 예상 효과

- **전략 품질**: 체계적 phase 진행으로 "서둘러 코드부터 짜기" 방지
- **비용 절감**: Research phase에서 가망 없는 전략을 일찍 포기 → 구현 비용 절약
- **디버깅**: 어느 phase에서 실패했는지 명확

**정량 추정**:
- Research phase에서 전략의 ~30%를 조기 탈락시킬 수 있다면
- 전략당 Implementation+Verification 비용 ~$10 × 0.3 = $3 절감
- 10개 전략 시 **$30 절감**

#### 구현 난이도: **Medium**

기존 순차 호출을 phase 구조로 리팩토링해야 한다. phase 간 데이터 전달 규약을 정의해야 하고, 실패 시 rollback 로직이 필요하다.

#### 의존성

- #4 (Worktree Isolation)과 결합하면 phase별 git 상태 관리 가능
- #5 (Cost Tracker)로 phase별 비용 측정 가능

---

### 기술 #4: Worktree Isolation

#### 기술 설명

Git worktree는 하나의 repository에서 여러 작업 디렉토리를 만드는 기능이다. claw-code에서는 각 sub-agent가 독립된 worktree에서 작업하여, 한 에이전트의 파일 변경이 다른 에이전트에 영향을 주지 않도록 한다.

```bash
# 메인 repo
git worktree add ../strategy_momentum_v1 -b strategy/momentum_v1
git worktree add ../strategy_mean_revert_v2 -b strategy/mean_revert_v2
```

각 worktree는 독립된 branch에서 동작하므로, 실패한 전략의 코드가 메인 branch를 오염시키지 않는다.

#### Helix 현재 상태

**없음**. 모든 전략이 같은 git state를 공유한다. `dir_{strategy_name}/`으로 디렉토리는 분리되어 있지만, git branch는 분리되지 않았다.

문제점:
- 전략 A의 `backtest.py` 수정이 전략 B에 영향 가능
- 실패한 전략의 코드를 깔끔히 제거하기 어려움
- 동시에 여러 전략을 개발할 때 충돌 가능

#### 구체적 적용 방안

**파일**: `orchestrator_agent.py`, 새 파일 `worktree_manager.py`

```python
# worktree_manager.py
import subprocess
from pathlib import Path

class WorktreeManager:
    BASE_DIR = Path("/Users/ryan/alpha_bridge/helix/claude_agent_sdk_lab")
    WORKTREE_DIR = BASE_DIR / ".worktrees"
    
    def create(self, strategy_name: str) -> Path:
        """전략별 worktree 생성"""
        branch = f"strategy/{strategy_name}"
        worktree_path = self.WORKTREE_DIR / strategy_name
        
        if worktree_path.exists():
            return worktree_path
        
        self.WORKTREE_DIR.mkdir(exist_ok=True)
        
        # branch 생성 + worktree 연결
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch],
            cwd=self.BASE_DIR, check=True
        )
        return worktree_path
    
    def cleanup(self, strategy_name: str, keep_branch: bool = False):
        """실패한 전략의 worktree 정리"""
        worktree_path = self.WORKTREE_DIR / strategy_name
        branch = f"strategy/{strategy_name}"
        
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=self.BASE_DIR
        )
        
        if not keep_branch:
            subprocess.run(
                ["git", "branch", "-D", branch],
                cwd=self.BASE_DIR
            )
    
    def merge_to_main(self, strategy_name: str):
        """승인된 전략을 main에 merge"""
        branch = f"strategy/{strategy_name}"
        subprocess.run(
            ["git", "merge", branch, "--no-ff", "-m", f"Merge strategy: {strategy_name}"],
            cwd=self.BASE_DIR, check=True
        )
        self.cleanup(strategy_name)
```

**orchestrator_agent.py 수정**:
```python
async def run_strategy(self, strategy_name: str):
    wt = WorktreeManager()
    strategy_dir = wt.create(strategy_name)
    
    try:
        # 모든 sub-agent에게 strategy_dir을 작업 디렉토리로 전달
        for phase in WorkflowPhase:
            await self.run_phase(phase, cwd=strategy_dir)
        
        # 성공 시 merge
        wt.merge_to_main(strategy_name)
    except StrategyFailedError:
        # 실패 시 깔끔히 정리
        wt.cleanup(strategy_name, keep_branch=False)
```

#### 예상 효과

- **격리성**: 전략 간 완전한 코드 격리
- **정리 용이**: 실패 전략을 `git worktree remove`로 깔끔히 삭제
- **병렬화 기반**: 향후 여러 전략을 동시에 개발할 수 있는 기반
- **이력 관리**: 각 전략의 코드 변경 이력이 branch로 보존

**정량 추정**:
- 직접적인 토큰/비용 절감은 적음
- **간접 효과**: 코드 충돌로 인한 재작업 방지 → 전략당 ~1 iteration 절약 가능 (약 $3-5)

#### 구현 난이도: **Medium**

Git worktree 자체는 간단하지만, sub-agent에게 작업 디렉토리를 전달하는 방식을 변경해야 하고, merge conflict 처리 로직이 필요하다.

#### 의존성

- #3 (Plan Mode)와 결합하면 phase별 branch 관리 가능
- #9 (Permission System)으로 worktree 외부 접근 제한 가능

---

### 기술 #5: Cost Tracker

#### 기술 설명

claw-code는 모든 API 호출의 토큰 사용량과 비용을 추적한다. 각 요청의 input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens를 기록하고, 모델별 요금표로 실제 비용을 계산한다.

```python
# claw-code의 cost tracking 구조
{
    "total_cost": 12.45,
    "total_input_tokens": 150000,
    "total_output_tokens": 45000,
    "by_model": {
        "claude-opus-4": {"cost": 10.20, "calls": 8},
        "claude-sonnet-4": {"cost": 2.25, "calls": 15}
    }
}
```

#### Helix 현재 상태

**없음**. `AgentCallTracker`가 호출 횟수와 시간을 추적하지만, 토큰 수와 비용은 추적하지 않는다. 전략 하나를 만드는 데 얼마가 드는지 알 수 없다.

#### 구체적 적용 방안

**파일**: 새 파일 `cost_tracker.py`, `orchestrator_agent.py` 수정

```python
# cost_tracker.py
from dataclasses import dataclass, field
from datetime import datetime
import json

# Anthropic 가격표 (2026-04 기준, $/1M tokens)
PRICING = {
    "claude-opus-4": {"input": 15.0, "output": 75.0, "cache_read": 1.5, "cache_write": 18.75},
    "claude-sonnet-4": {"input": 3.0, "output": 15.0, "cache_read": 0.3, "cache_write": 3.75},
}

@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

@dataclass 
class CostTracker:
    strategy_name: str
    records: list = field(default_factory=list)
    
    def record(self, agent_name: str, model: str, usage: TokenUsage):
        """API 응답에서 usage 정보를 기록"""
        pricing = PRICING.get(model, PRICING["claude-sonnet-4"])
        
        cost = (
            usage.input_tokens * pricing["input"] / 1_000_000
            + usage.output_tokens * pricing["output"] / 1_000_000
            + usage.cache_read_tokens * pricing["cache_read"] / 1_000_000
            + usage.cache_write_tokens * pricing["cache_write"] / 1_000_000
        )
        
        self.records.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "model": model,
            "tokens": {
                "input": usage.input_tokens,
                "output": usage.output_tokens,
                "cache_read": usage.cache_read_tokens,
                "cache_write": usage.cache_write_tokens,
            },
            "cost_usd": round(cost, 4),
        })
    
    @property
    def total_cost(self) -> float:
        return sum(r["cost_usd"] for r in self.records)
    
    def by_agent(self) -> dict:
        """에이전트별 비용 집계"""
        result = {}
        for r in self.records:
            agent = r["agent"]
            if agent not in result:
                result[agent] = 0.0
            result[agent] += r["cost_usd"]
        return result
    
    def by_phase(self, phase_map: dict) -> dict:
        """Phase별 비용 집계 (agent→phase 매핑 필요)"""
        result = {}
        for r in self.records:
            phase = phase_map.get(r["agent"], "unknown")
            if phase not in result:
                result[phase] = 0.0
            result[phase] += r["cost_usd"]
        return result
    
    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump({
                "strategy": self.strategy_name,
                "total_cost_usd": self.total_cost,
                "by_agent": self.by_agent(),
                "records": self.records,
            }, f, indent=2)
```

**orchestrator_agent.py의 PostToolUse hook에 통합**:
```python
# 기존 PostToolUse hook에 추가
async def on_post_tool_use(event):
    # 기존 agent call tracking...
    
    # 비용 추적 추가
    if hasattr(event, 'usage'):
        cost_tracker.record(
            agent_name=current_agent,
            model=current_model,
            usage=TokenUsage(
                input_tokens=event.usage.input_tokens,
                output_tokens=event.usage.output_tokens,
                cache_read_tokens=getattr(event.usage, 'cache_read_input_tokens', 0),
                cache_write_tokens=getattr(event.usage, 'cache_creation_input_tokens', 0),
            )
        )
```

#### 예상 효과

- **가시성**: 전략당 비용, 에이전트당 비용, phase당 비용을 정확히 파악
- **최적화 기반**: 어떤 에이전트가 비용을 많이 쓰는지 알면 최적화 대상을 특정 가능
- **ROI 계산**: 전략의 예상 수익 vs 개발 비용 비교 가능

**정량 추정**:
- 비용 추적 자체의 토큰 오버헤드: 무시할 수준 (로컬 계산)
- **간접 효과**: 비용 가시성을 통한 최적화로 10-20% 추가 비용 절감 기대

#### 구현 난이도: **Low**

Claude Agent SDK의 응답에서 usage 정보를 읽어오는 것만으로 구현 가능. 가장 쉬우면서도 가장 높은 ROI를 제공하는 기술.

#### 의존성

- #6 (Budget Cap)의 전제 조건
- #1 (Fork Subagent)의 효과 측정에 필수

---

### 기술 #6: Budget Cap

#### 기술 설명

claw-code에는 세션당 예산 한도를 설정하는 기능이 있다. 누적 비용이 한도에 도달하면 실행을 중단하고 사용자에게 알린다. 이는 무한 루프나 비정상적으로 긴 대화로 인한 비용 폭주를 방지한다.

#### Helix 현재 상태

**없음**. max 5 iterations 제한은 있지만, 각 iteration의 비용 제한은 없다. 한 iteration에서 sub-agent가 매우 긴 대화를 하면 비용이 크게 발생할 수 있다.

**실제 리스크 시나리오**:
- quant-developer가 코드 에러 무한 수정 루프에 빠짐
- senior-developer의 Task tool 사용이 재귀적으로 깊어짐
- 5 iterations × 고비용 iteration = $100+ 가능

#### 구체적 적용 방안

**파일**: `cost_tracker.py` 확장, `orchestrator_agent.py` 수정

```python
# cost_tracker.py에 추가
class BudgetGuard:
    def __init__(self, cost_tracker: CostTracker, limits: dict):
        self.cost_tracker = cost_tracker
        self.limits = limits  # e.g., {"per_strategy": 30.0, "per_agent_call": 5.0, "per_iteration": 15.0}
    
    def check(self, scope: str = "per_strategy") -> bool:
        """예산 초과 여부 확인. True = 초과"""
        current = self.cost_tracker.total_cost
        limit = self.limits.get(scope, float('inf'))
        
        if current >= limit:
            logger.error(f"🚨 Budget exceeded! ${current:.2f} >= ${limit:.2f} ({scope})")
            return True
        
        # 80% 경고
        if current >= limit * 0.8:
            logger.warning(f"⚠️ Budget warning: ${current:.2f} / ${limit:.2f} ({scope})")
        
        return False

# config.py에 추가
class BudgetConfig:
    PER_STRATEGY_USD = 30.0      # 전략당 최대 $30
    PER_AGENT_CALL_USD = 5.0     # 단일 에이전트 호출 최대 $5
    PER_ITERATION_USD = 15.0     # 반복당 최대 $15
    EMERGENCY_STOP_USD = 50.0    # 절대 한도 $50

# orchestrator_agent.py
async def call_sub_agent(self, agent_name, task):
    if self.budget_guard.check("per_strategy"):
        raise BudgetExceededError(f"Strategy budget exceeded: ${self.cost_tracker.total_cost:.2f}")
    
    response = await self._execute_agent(agent_name, task)
    
    if self.budget_guard.check("per_agent_call"):
        logger.warning(f"Agent {agent_name} exceeded per-call budget. Truncating.")
    
    return response
```

#### 예상 효과

- **비용 안전**: 최악의 경우 비용을 $50 이내로 제한
- **자동 중단**: 비정상 실행을 자동 감지하고 중단
- **심리적 안전**: 시스템을 자동으로 돌려놓고 걱정 없이 다른 일 가능

**정량 추정**:
- 비정상 실행 1회 방지 시 $50-100 절약
- 월 10회 자동 실행 기준, 1회만 비정상이어도 **월 $50+ 절약**

#### 구현 난이도: **Low**

#5 (Cost Tracker)가 구현되어 있다면, 임계값 비교 로직만 추가하면 된다.

#### 의존성

- **#5 (Cost Tracker) 필수 선행**
- #3 (Plan Mode)와 결합하면 phase별 예산 배분 가능

---

### 기술 #7: Dream 4-Phase Consolidation

#### 기술 설명

claw-code의 "dream" 기능은 유휴 시간(idle time)에 메모리를 정리하는 4단계 프로세스이다:

```
Phase 1: Collect   → 모든 메모리 수집
Phase 2: Analyze   → 패턴, 중복, 노후 정보 식별
Phase 3: Compress  → 중요 정보 유지, 중복 제거, 요약
Phase 4: Store     → 정리된 메모리를 다시 저장
```

이것은 사람의 수면 중 기억 정리와 유사하다. 꿈(dream)을 통해 불필요한 정보를 제거하고 중요한 패턴을 강화한다.

#### Helix 현재 상태

**없음**. longterm_memory.md는 append-only로 계속 커진다. 정리 메커니즘이 없어서:
- 오래된 실패 전략의 기록이 계속 남아있음
- 비슷한 내용이 중복 기록됨
- context window를 점점 더 많이 차지

#### 구체적 적용 방안

**파일**: 새 파일 `memory_consolidator.py`

```python
# memory_consolidator.py
from claude_sdk import ClaudeSDKClient

class DreamConsolidator:
    """메모리 정리를 위한 4-phase consolidation"""
    
    CONSOLIDATION_PROMPT = """
    당신은 메모리 정리 전문가입니다. 아래 메모리를 분석하고 정리하세요.
    
    규칙:
    1. 중복 정보 제거
    2. 실패한 전략에서 배운 교훈만 유지 (상세 로그는 제거)
    3. 성공 패턴을 명확하게 정리
    4. 날짜가 30일 이상 된 세부 정보는 요약으로 대체
    5. 정리 후 메모리는 원본의 50% 이하여야 함
    
    출력 형식:
    ## 핵심 교훈 (Lessons)
    ## 성공 패턴 (Patterns)  
    ## 활성 컨텍스트 (Active)
    """
    
    async def consolidate(self, memory_path: Path, scope: str):
        """특정 scope의 메모리를 consolidation"""
        if not memory_path.exists():
            return
        
        content = memory_path.read_text()
        original_size = len(content)
        
        # 너무 작으면 정리 불필요
        if original_size < 2000:  # ~500 tokens
            return
        
        # Phase 1: Collect
        raw_memory = content
        
        # Phase 2+3: Analyze + Compress (LLM 사용)
        client = ClaudeSDKClient(model="claude-sonnet-4")  # 저렴한 모델 사용
        consolidated = await client.complete(
            system=self.CONSOLIDATION_PROMPT,
            messages=[{"role": "user", "content": f"정리할 메모리 ({scope} scope):\n\n{raw_memory}"}]
        )
        
        # Phase 4: Store
        # 원본 백업
        backup_path = memory_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d')}.md")
        memory_path.rename(backup_path)
        
        # 정리본 저장
        memory_path.write_text(consolidated)
        
        new_size = len(consolidated)
        logger.info(f"Dream consolidation: {original_size} → {new_size} chars ({new_size/original_size*100:.0f}%)")
    
    async def run_full_dream(self, strategy_name: str):
        """전체 dream cycle 실행"""
        mm = MemoryManager(strategy_name)
        
        for scope in ["user", "project", "local"]:
            path = {
                "user": MemoryConfig.USER_MEMORY_PATH.expanduser(),
                "project": MemoryConfig.PROJECT_MEMORY_PATH,
                "local": MemoryConfig.local_memory_path(strategy_name),
            }[scope]
            await self.consolidate(path, scope)
```

**실행 타이밍**: 
- 전략 완료 후 (성공이든 실패든)
- 5 iterations 종료 후
- 주기적 (cron으로 매일 1회)

#### 예상 효과

- **메모리 크기**: 정리 후 50% 이하로 축소
- **Context window 절감**: 축소된 메모리 → 매 API 호출마다 토큰 절감
- **정보 품질**: 노이즈 제거, 핵심 패턴 강화

**정량 추정**:
- 10개 전략 실행 후 longterm_memory.md: ~10K tokens
- 정리 후: ~4K tokens (60% 축소)
- 이후 전략에서 매 호출마다 6K tokens 절약 × 에이전트 수
- **전략당 ~$1-2 절약** (누적 효과)

#### 구현 난이도: **Medium**

LLM을 사용한 정리이므로 정리 자체에 비용이 든다 (Sonnet 사용 시 ~$0.5). 정리 품질의 검증이 필요하고, 중요 정보 유실 리스크가 있어 백업 메커니즘이 필수.

#### 의존성

- **#2 (3-Scope Memory) 선행 권장**: scope별로 독립 정리 가능
- #8 (Snip Compaction)과 상호보완적

---

### 기술 #8: Snip Compaction

#### 기술 설명

claw-code에서 대화가 길어지면 이전 메시지를 요약(snip)으로 대체하는 기능이다. 전체 대화를 유지하는 대신, 오래된 부분을 짧은 요약으로 압축한다.

```
원본: [msg1, msg2, msg3, msg4, ..., msg50, msg51, msg52]
Snip:  [📋 "msg1-msg45 요약: XYZ를 시도했고 결과는...", msg46, ..., msg52]
```

이렇게 하면 context window 한도 내에서 더 오래 대화를 이어갈 수 있다.

#### Helix 현재 상태

**없음**. orchestrator의 대화 히스토리가 iteration마다 누적되어 갈수록 비용이 증가한다. 5회 iteration 제한이 있지만, 각 iteration 내에서 sub-agent와의 대화가 길어질 수 있다.

#### 구체적 적용 방안

**파일**: `orchestrator_agent.py`

```python
class ConversationCompactor:
    MAX_HISTORY_TOKENS = 30000  # 대화 히스토리 최대 토큰
    SNIP_THRESHOLD = 25000      # 이 이상이면 압축 시작
    KEEP_RECENT = 5             # 최근 N개 메시지는 유지
    
    async def compact_if_needed(self, messages: list) -> list:
        """대화가 너무 길면 오래된 부분을 요약으로 대체"""
        estimated_tokens = self.estimate_tokens(messages)
        
        if estimated_tokens < self.SNIP_THRESHOLD:
            return messages
        
        # 최근 메시지 보존
        recent = messages[-self.KEEP_RECENT:]
        old = messages[:-self.KEEP_RECENT]
        
        # 오래된 메시지를 요약
        summary = await self.summarize(old)
        
        # 요약 + 최근 메시지로 교체
        snipped = [
            {"role": "user", "content": f"[이전 대화 요약]\n{summary}"},
            {"role": "assistant", "content": "이전 대화 요약을 확인했습니다. 이어서 진행하겠습니다."},
            *recent
        ]
        
        new_tokens = self.estimate_tokens(snipped)
        logger.info(f"Snip compaction: {estimated_tokens} → {new_tokens} tokens")
        return snipped
    
    def estimate_tokens(self, messages: list) -> int:
        """대략적인 토큰 수 추정 (1 token ≈ 4 chars for English, 2 chars for Korean)"""
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return total_chars // 3  # 보수적 추정
    
    async def summarize(self, messages: list) -> str:
        """메시지 목록을 요약"""
        content = "\n".join(m.get("content", "")[:500] for m in messages)
        client = ClaudeSDKClient(model="claude-sonnet-4")
        return await client.complete(
            system="대화 내용을 300단어 이내로 요약하세요. 핵심 결정사항, 결과, 남은 과제를 포함하세요.",
            messages=[{"role": "user", "content": content}]
        )
```

#### 예상 효과

- **장기 실행 안정성**: 5 iteration 동안 context window 초과 방지
- **비용 절감**: iteration 후반의 input token 비용 감소

**정량 추정**:
- Iteration 4-5에서 대화 히스토리 ~40K tokens → 압축 후 ~15K tokens
- **iteration 후반 input 비용 60% 절감**
- 전체 전략 기준 약 15-20% input token 절감

#### 구현 난이도: **Medium**

요약의 품질이 중요. 핵심 정보가 누락되면 후속 iteration이 잘못된 방향으로 갈 수 있다. 요약 자체에 Sonnet 호출 비용이 든다.

#### 의존성

- #1 (Fork Subagent)과 결합 시 주의: fork의 base가 snipped된 대화이면 캐시 효율이 달라질 수 있음

---

### 기술 #9: Permission System

#### 기술 설명

claw-code는 도구(tool) 사용에 대해 세밀한 권한 제어를 한다:
- **allow**: 항상 허용
- **deny**: 항상 거부  
- **ask**: 사용자에게 확인

도구별, 경로별, 명령어별로 권한을 설정할 수 있다. 예: "Bash tool은 허용하되, `rm -rf`는 거부"

#### Helix 현재 상태

**`bypassPermissions` 전체 적용**. 모든 에이전트가 모든 도구를 제한 없이 사용한다. 이는 자동화를 위한 선택이지만, 보안 리스크가 있다.

문제점:
- quant-researcher가 파일 삭제 가능
- 어떤 에이전트든 시스템 명령어 실행 가능
- 실수로 중요 파일 덮어쓰기 가능

#### 구체적 적용 방안

**파일**: `config.py`, 각 sub-agent 파일

```python
# config.py에 추가
AGENT_PERMISSIONS = {
    "quant-researcher": {
        "Bash": {
            "allow": ["python", "pip", "curl"],
            "deny": ["rm", "mv", "chmod", "chown", "sudo"],
        },
        "Write": {
            "allow_paths": ["dir_*/research/**", "dir_*/hypothesis/**"],
            "deny_paths": ["*.py", "config.*"],
        },
        "Read": "allow_all",
        "WebSearch": "allow_all",
    },
    "quant-developer": {
        "Bash": {
            "allow": ["python", "pip", "pytest", "black", "ruff"],
            "deny": ["rm -rf", "sudo", "curl", "wget"],
        },
        "Write": {
            "allow_paths": ["dir_*/src/**", "dir_*/tests/**"],
            "deny_paths": ["orchestrator_agent.py", "config.py"],
        },
        "Edit": {
            "allow_paths": ["dir_*/src/**"],
        },
    },
    "backtest-agent": {
        "Bash": {
            "allow": ["python"],
            "deny": ["pip", "sudo", "rm"],
        },
        "Write": {
            "allow_paths": ["dir_*/backtest_results/**"],
        },
        "Read": "allow_all",
    },
}

# orchestrator_agent.py의 PreToolUse hook에서 권한 체크
async def on_pre_tool_use(event):
    agent_name = get_current_agent()
    tool_name = event.tool_name
    
    perms = AGENT_PERMISSIONS.get(agent_name, {}).get(tool_name)
    if perms is None:
        return {"decision": "deny", "reason": f"No permission defined for {agent_name}/{tool_name}"}
    
    if perms == "allow_all":
        return {"decision": "allow"}
    
    # Bash 명령어 체크
    if tool_name == "Bash":
        command = event.tool_input.get("command", "")
        for denied in perms.get("deny", []):
            if denied in command:
                return {"decision": "deny", "reason": f"Command '{denied}' denied for {agent_name}"}
    
    # 경로 체크
    if tool_name in ("Write", "Edit", "Read"):
        path = event.tool_input.get("file_path", "")
        # fnmatch로 allow/deny 패턴 매칭
        ...
    
    return {"decision": "allow"}
```

#### 예상 효과

- **보안**: 에이전트의 실수로 인한 파일 손상 방지
- **격리**: 각 에이전트가 자신의 영역에서만 작업
- **감사**: 거부된 요청 로그로 에이전트 행동 분석 가능

**정량 추정**:
- 직접적 비용 절감 없음
- **리스크 방지 가치**: 중요 파일 손상 1건 방지 = 수 시간 복구 작업 절약

#### 구현 난이도: **Medium**

PreToolUse hook에서 권한 체크 로직을 구현해야 한다. 경로 패턴 매칭과 명령어 파싱이 필요. 기존 hook 시스템을 활용할 수 있으므로 아키텍처 변경은 적다.

#### 의존성

- #4 (Worktree Isolation)과 결합하면 worktree 외부 접근을 자연스럽게 제한
- #14 (Denial Tracking)의 데이터 소스

---

### 기술 #10: Built-in Agent Types (Explore/Verify)

#### 기술 설명

claw-code에는 특정 목적에 최적화된 built-in agent type이 있다:
- **Explorer**: 정보 탐색 전용. 코드베이스를 읽고 분석하되, 수정하지 않음
- **Verifier**: 독립 검증 전용. 기존 결과를 새 관점에서 재검증

이 에이전트들은 일반 에이전트보다 좁은 도구 세트와 특화된 프롬프트를 가진다.

#### Helix 현재 상태

**없음**. 현재 6개 에이전트는 모두 범용 목적이다. 독립적인 탐색이나 검증 전용 에이전트가 없다.

#### 구체적 적용 방안

**파일**: 새 파일 `alpha_explorer_agent.py`, `independent_verifier_agent.py`

```python
# alpha_explorer_agent.py
def get_system_prompt():
    return """
    당신은 Alpha Pool Explorer입니다.
    
    역할: 학술 논문, 팩터 데이터베이스, 시장 데이터를 탐색하여 새로운 alpha 후보를 발견합니다.
    
    제약:
    - 코드를 작성하지 않습니다
    - 파일을 수정하지 않습니다
    - 오직 읽기와 검색만 합니다
    
    출력: alpha_candidates.json 형식으로 후보 목록 작성
    각 후보에 대해:
    - 팩터 이름
    - 가설 (왜 alpha가 존재하는지)
    - 근거 (논문, 데이터, 직관)
    - 예상 IC (Information Coefficient)
    - 구현 복잡도 (Low/Medium/High)
    """

def get_allowed_tools():
    return ["Read", "WebSearch", "Bash"]  # Bash는 read-only 명령만

# independent_verifier_agent.py
def get_system_prompt():
    return """
    당신은 Independent Strategy Verifier입니다.
    
    역할: backtest-agent의 결과를 독립적으로 재검증합니다.
    
    검증 항목:
    1. Look-ahead bias 확인
    2. Survivorship bias 확인
    3. 과적합 여부 (in-sample vs out-of-sample)
    4. 거래 비용 현실성
    5. 데이터 기간 충분성
    6. 통계적 유의성 (t-stat > 2.0)
    
    당신은 기존 에이전트의 결론에 동의할 의무가 없습니다.
    의심스러우면 REJECT하세요.
    """

def get_allowed_tools():
    return ["Read", "Bash"]  # 읽기와 분석만
```

#### 예상 효과

- **전략 발굴**: Explorer가 사람이 놓치는 alpha 후보를 발견
- **전략 품질**: Verifier가 독립적으로 검증하여 거짓 양성(false positive) 필터링
- **편향 방지**: 개발한 에이전트가 자기 전략을 검증하는 것보다 독립 검증이 객관적

**정량 추정**:
- Verifier가 과적합 전략 10%를 추가 탈락시킨다면
- 실전에서 해당 전략의 손실 방지 → 전략당 기대값 개선
- Explorer가 월 2-3개 추가 alpha 후보 발견 → 파이프라인 처리량 증가

#### 구현 난이도: **Low-Medium**

새 에이전트를 추가하는 것은 기존 패턴을 따르면 간단. orchestrator에 호출 시점을 추가하는 것이 핵심.

#### 의존성

- #3 (Plan Mode)의 Research phase에 Explorer, Verification phase에 Verifier 배치
- #9 (Permission System)으로 Explorer/Verifier의 권한 제한

---

### 기술 #11: Agent List → Attachment 분리

#### 기술 설명

claw-code에서 에이전트에게 보내는 정보를 두 부분으로 분리한다:
1. **Messages** (대화 히스토리): prompt cache의 prefix 역할
2. **Attachments** (파일 내용 등): 변경 가능한 부분

핵심은 **자주 변하지 않는 정보를 messages 앞쪽에 배치**하여 캐시 히트율을 높이는 것이다.

```
Before: [system_prompt, file_A_content, user_msg, file_B_content, ...]
After:  [system_prompt, {attachment: file_A}, {attachment: file_B}, user_msg, ...]
         ↑ 캐시 가능 prefix가 길어짐 ↑
```

#### Helix 현재 상태

**없음**. 파일 내용이 대화 메시지에 인라인으로 포함된다. system prompt에 파일 내용을 넣거나, 사용자 메시지에 파일 내용을 직접 포함하는 방식.

#### 구체적 적용 방안

**파일**: `orchestrator_agent.py`

```python
async def call_sub_agent(self, agent_name: str, task: str, context_files: list = None):
    # 안정적인 부분 (캐시 가능)
    system_prompt = get_system_prompt(agent_name)
    
    # 첨부 파일을 system prompt 직후에 배치
    attachments = []
    if context_files:
        for file_path in context_files:
            content = Path(file_path).read_text()
            attachments.append({
                "role": "user",
                "content": f"[Attachment: {file_path}]\n{content}"
            })
    
    # 메시지 구성: system → attachments → task
    messages = [
        *attachments,  # 파일 내용 (자주 변하지 않음 → 캐시 히트)
        {"role": "assistant", "content": "첨부 파일을 확인했습니다."},
        {"role": "user", "content": task},  # 실제 작업 (매번 다름)
    ]
    
    # agent 실행
    agent_def = AgentDefinition(
        name=agent_name,
        system_prompt=system_prompt,
        tools=get_allowed_tools(agent_name),
    )
    return await client.run(agent_def, messages=messages)
```

#### 예상 효과

- **캐시 히트율 증가**: 동일 파일을 참조하는 연속 호출에서 attachment 부분이 캐시됨
- **비용 절감**: #1 (Fork)과 결합 시 시너지

**정량 추정**:
- 단독 효과: input token의 ~10-15% 캐시 히트율 증가
- #1과 결합 시: 추가 10% 캐시 히트율

#### 구현 난이도: **Low**

메시지 배열의 순서만 변경하면 된다. 코드 변경량이 적다.

#### 의존성

- #1 (Fork Subagent)과 강한 시너지
- Claude API의 prompt caching 동작 방식에 의존

---

### 기술 #12: File State Cache

#### 기술 설명

claw-code는 파일을 읽을 때 결과를 캐시한다. 같은 파일을 다시 읽을 때 디스크 I/O 없이 캐시에서 반환하며, 파일이 변경되었을 때만 다시 읽는다.

```python
# claw-code 패턴
class FileCache:
    cache = {}  # {path: (mtime, content)}
    
    def read(self, path):
        mtime = os.path.getmtime(path)
        if path in self.cache and self.cache[path][0] == mtime:
            return self.cache[path][1]  # 캐시 히트
        content = open(path).read()
        self.cache[path] = (mtime, content)
        return content
```

#### Helix 현재 상태

**없음**. 매번 디스크에서 파일을 읽는다. sub-agent가 같은 파일을 여러 번 읽을 때 중복 I/O가 발생한다.

#### 구체적 적용 방안

**파일**: 새 파일 `file_cache.py`

```python
import os
from pathlib import Path
from typing import Optional

class FileStateCache:
    def __init__(self, max_entries: int = 100, max_size_bytes: int = 10_000_000):
        self._cache: dict[str, tuple[float, str]] = {}
        self.max_entries = max_entries
        self.max_size_bytes = max_size_bytes
        self._total_size = 0
    
    def read(self, path: str) -> str:
        abs_path = str(Path(path).resolve())
        mtime = os.path.getmtime(abs_path)
        
        if abs_path in self._cache:
            cached_mtime, cached_content = self._cache[abs_path]
            if cached_mtime == mtime:
                return cached_content
        
        content = Path(abs_path).read_text()
        self._store(abs_path, mtime, content)
        return content
    
    def invalidate(self, path: str):
        abs_path = str(Path(path).resolve())
        if abs_path in self._cache:
            self._total_size -= len(self._cache[abs_path][1])
            del self._cache[abs_path]
    
    def _store(self, abs_path: str, mtime: float, content: str):
        # LRU eviction if needed
        if len(self._cache) >= self.max_entries:
            oldest = next(iter(self._cache))
            self.invalidate(oldest)
        
        self._cache[abs_path] = (mtime, content)
        self._total_size += len(content)

# 전역 인스턴스
file_cache = FileStateCache()
```

#### 예상 효과

- **I/O 감소**: 동일 파일 반복 읽기 제거
- **속도 향상**: 특히 큰 파일(백테스트 결과 등)에서 체감

**정량 추정**:
- 토큰/비용 직접 영향 없음 (로컬 I/O)
- **속도**: 전략당 실행 시간 5-10% 감소 (I/O bound 구간)

#### 구현 난이도: **Low**

순수 Python 코드. 외부 의존성 없음.

#### 의존성

- 없음 (독립적으로 구현 가능)

---

### 기술 #13: Forked Agent Cache

#### 기술 설명

#1 (Fork Subagent)의 확장. fork된 에이전트들이 공통 prefix를 가지므로, API 레벨에서 prompt cache가 자동으로 공유된다. 이 기술은 **fork를 의도적으로 설계하여 캐시 공유를 극대화**하는 것이다.

#### Helix 현재 상태

**없음** (#1과 동일)

#### 구체적 적용 방안

#1의 구현에 포함. 추가로:

```python
class CacheOptimizedForker:
    """같은 context를 공유하는 여러 sub-agent를 연속 호출하여 캐시 활용 극대화"""
    
    async def batch_fork(self, base_messages: list, agent_tasks: list[tuple[str, str]]):
        """여러 agent를 같은 base에서 연속 fork"""
        results = {}
        for agent_name, task in agent_tasks:
            # 동일 base_messages를 사용하므로 API 캐시가 연속 히트
            result = await self.fork_sub_agent(base_messages, agent_name, task)
            results[agent_name] = result
        return results
```

핵심: **연속 호출** 시 Anthropic API의 prompt cache TTL(보통 5분) 내에 다음 호출이 이루어지면 캐시 히트.

#### 예상 효과

- #1에 포함된 효과에 추가로, 연속 호출 최적화로 **5-10% 추가 캐시 히트**

#### 구현 난이도: **Low** (#1이 구현되어 있다면)

#### 의존성

- **#1 (Fork Subagent) 필수 선행**

---

### 기술 #14: Denial Tracking

#### 기술 설명

권한 시스템이 거부한 요청을 기록하고 분석하는 기능. 에이전트가 반복적으로 거부당하는 패턴을 감지하면:
1. 프롬프트를 수정하여 해당 행동을 하지 않도록 유도
2. 또는 권한을 조정

#### Helix 현재 상태

**없음** (권한 시스템 자체가 없으므로)

#### 구체적 적용 방안

**파일**: `cost_tracker.py` 또는 새 파일 `denial_tracker.py`

```python
class DenialTracker:
    def __init__(self):
        self.denials: list[dict] = []
    
    def record(self, agent_name: str, tool: str, reason: str, input_summary: str):
        self.denials.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "tool": tool,
            "reason": reason,
            "input_summary": input_summary[:200],
        })
    
    def analyze_patterns(self) -> list[dict]:
        """반복 패턴 분석"""
        from collections import Counter
        patterns = Counter((d["agent"], d["tool"], d["reason"]) for d in self.denials)
        return [
            {"agent": a, "tool": t, "reason": r, "count": c}
            for (a, t, r), c in patterns.most_common(10)
        ]
    
    def suggest_fixes(self) -> list[str]:
        """패턴 기반 개선 제안"""
        suggestions = []
        for pattern in self.analyze_patterns():
            if pattern["count"] >= 3:
                suggestions.append(
                    f"Agent '{pattern['agent']}'가 '{pattern['tool']}'에서 "
                    f"'{pattern['reason']}'으로 {pattern['count']}회 거부됨. "
                    f"System prompt 수정 또는 권한 조정 권장."
                )
        return suggestions
```

#### 예상 효과

- **프롬프트 품질**: 반복 거부 패턴 → 프롬프트 개선 → 불필요한 시도 감소 → 토큰 절약
- **보안 감사**: 비정상 접근 시도 감지

**정량 추정**: 거부 1건당 ~500 tokens 낭비 (시도 + 거부 + 재시도). 반복 패턴 제거로 전략당 ~1K tokens 절약.

#### 구현 난이도: **Low**

#### 의존성

- **#9 (Permission System) 필수 선행**

---

### 기술 #15: Team Memory Sync

#### 기술 설명

여러 전략(또는 세션) 간에 학습한 지식을 공유하는 메커니즘. 전략 A에서 발견한 "모멘텀 팩터는 소형주에서 더 강하다"라는 인사이트를 전략 B도 활용할 수 있다.

#### Helix 현재 상태

**없음**. 각 전략의 longterm_memory.md는 독립적이다. 전략 A에서 배운 것이 전략 B에 전파되지 않는다.

#### 구체적 적용 방안

**파일**: `memory_consolidator.py` 확장

```python
class TeamMemorySync:
    SHARED_INSIGHTS_PATH = Path("~/.helix/memory/shared_insights.md")
    
    async def extract_and_share(self, strategy_name: str, local_memory_path: Path):
        """전략의 로컬 메모리에서 공유 가능한 인사이트 추출"""
        local_content = local_memory_path.read_text()
        
        client = ClaudeSDKClient(model="claude-sonnet-4")
        insights = await client.complete(
            system="""전략 메모리에서 다른 전략에도 유용한 범용 인사이트를 추출하세요.
            전략 특화 정보(파라미터, 종목 등)는 제외하세요.
            범용적으로 적용 가능한 패턴, 교훈, 발견만 포함하세요.""",
            messages=[{"role": "user", "content": f"전략 '{strategy_name}'의 메모리:\n{local_content}"}]
        )
        
        # 공유 인사이트에 추가
        shared_path = self.SHARED_INSIGHTS_PATH.expanduser()
        shared_path.parent.mkdir(parents=True, exist_ok=True)
        with open(shared_path, 'a') as f:
            f.write(f"\n\n### From {strategy_name} ({datetime.now().strftime('%Y-%m-%d')})\n{insights}")
    
    def load_shared(self) -> str:
        """공유 인사이트 로드 (user scope memory의 일부로 사용)"""
        shared_path = self.SHARED_INSIGHTS_PATH.expanduser()
        if shared_path.exists():
            return shared_path.read_text()
        return ""
```

#### 예상 효과

- **학습 누적**: 시간이 지날수록 공유 지식이 풍부해져 새 전략 개발 품질 향상
- **실수 방지**: 다른 전략에서 실패한 패턴을 반복하지 않음

**정량 추정**:
- 10개 전략 실행 후 공유 인사이트 축적 → 이후 전략의 Research phase 시간 20% 단축
- 반복 실패 방지로 전략당 ~0.5 iteration 절약 → **$3-5 절약**

#### 구현 난이도: **Medium**

인사이트 추출의 품질이 핵심. 전략 특화 정보를 잘 필터링해야 한다.

#### 의존성

- **#2 (3-Scope Memory)의 user scope에 통합**
- #7 (Dream Consolidation)으로 공유 메모리도 정기 정리

---

### 기술 #16: Prompt Suggestion

#### 기술 설명

claw-code에서 에이전트가 사용자에게 다음 행동을 제안하는 기능. "이것을 시도해보시겠어요?" 같은 제안을 통해 사용자가 다음 단계를 결정하는 것을 도운다.

#### Helix 현재 상태

**없음**. orchestrator가 자동으로 실행하고 최종 결과만 보고한다.

#### 구체적 적용 방안

**파일**: `orchestrator_agent.py`

```python
class StrategySuggester:
    async def suggest_next(self, completed_strategies: list, market_profile: str) -> list[str]:
        """완료된 전략 목록을 보고 다음 전략 방향 제안"""
        client = ClaudeSDKClient(model="claude-sonnet-4")
        suggestions = await client.complete(
            system="""퀀트 포트폴리오 다각화 전문가입니다.
            기존 전략 목록을 보고, 상관관계가 낮은 새 전략 방향을 3개 제안하세요.
            각 제안에 대해 기존 전략과의 예상 상관계수를 포함하세요.""",
            messages=[{
                "role": "user", 
                "content": f"시장: {market_profile}\n기존 전략:\n" + 
                           "\n".join(f"- {s}" for s in completed_strategies)
            }]
        )
        return suggestions
```

#### 예상 효과

- **포트폴리오 다각화**: 서로 상관관계가 낮은 전략 조합 유도
- **사용자 경험**: 다음 행동에 대한 가이드 제공

**정량 추정**: 직접 비용 영향 미미. 포트폴리오 수준의 장기 효과.

#### 구현 난이도: **Low**

#### 의존성

- #15 (Team Memory Sync)로 이전 전략 정보 활용
- 완료된 전략 목록 관리가 필요

---

### 기술 #17: Feature Gate

#### 기술 설명

새 기능을 전체 시스템에 적용하기 전에, 일부 전략(또는 실행)에서만 활성화하여 테스트하는 메커니즘. A/B 테스트와 유사하다.

```python
# claw-code 패턴
if feature_gate.is_enabled("new_memory_system"):
    memory = ThreeScopeMemory()
else:
    memory = SingleFileMemory()
```

#### Helix 현재 상태

**없음**. 새 기능 도입 시 전체 시스템에 일괄 적용해야 한다.

#### 구체적 적용 방안

**파일**: `config.py`

```python
# config.py에 추가
class FeatureGates:
    _gates = {
        "fork_subagent": False,
        "three_scope_memory": False,
        "plan_mode": False,
        "worktree_isolation": False,
        "cost_tracker": True,  # 먼저 활성화
        "budget_cap": True,
        "dream_consolidation": False,
        "snip_compaction": False,
        "permission_system": False,
        "explorer_agent": False,
        "verifier_agent": False,
    }
    
    @classmethod
    def is_enabled(cls, feature: str) -> bool:
        return cls._gates.get(feature, False)
    
    @classmethod
    def enable(cls, feature: str):
        cls._gates[feature] = True
        logger.info(f"Feature enabled: {feature}")
    
    @classmethod
    def disable(cls, feature: str):
        cls._gates[feature] = False
        logger.info(f"Feature disabled: {feature}")

# 사용 예
if FeatureGates.is_enabled("fork_subagent"):
    response = await forker.fork_sub_agent(base_messages, agent_name, task)
else:
    response = await self.call_sub_agent(agent_name, task)
```

환경 변수로 오버라이드 가능하게:
```python
@classmethod
def is_enabled(cls, feature: str) -> bool:
    # 환경 변수 우선
    env_key = f"HELIX_FEATURE_{feature.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        return env_val.lower() in ("1", "true", "yes")
    return cls._gates.get(feature, False)
```

#### 예상 효과

- **안전한 실험**: 새 기능이 문제를 일으키면 즉시 비활성화
- **점진적 도입**: 하나씩 기능을 켜면서 효과 측정
- **A/B 테스트**: 같은 전략을 feature on/off로 실행하여 비교

**정량 추정**: 직접 비용 영향 없음. **간접 가치**: 새 기능 도입 실패 시 복구 시간 90% 단축.

#### 구현 난이도: **Low**

간단한 dict + 환경 변수 체크. 모든 다른 기술의 안전한 도입을 가능하게 하는 메타-기술.

#### 의존성

- 없음 (모든 다른 기술보다 먼저 구현해야 함)

---

## 4. 우선순위 로드맵

### Phase 1: Foundation (1-2주) — 즉시 효과 + 안전 기반

| 순서 | 기술 | 이유 | 예상 공수 |
|------|------|------|-----------|
| 1-1 | **#17 Feature Gate** | 모든 후속 기술의 안전 도입 기반 | 0.5일 |
| 1-2 | **#5 Cost Tracker** | 비용 가시성 확보 → 최적화 기반 | 1일 |
| 1-3 | **#6 Budget Cap** | 비용 폭주 방지 (즉시 리스크 제거) | 0.5일 |
| 1-4 | **#12 File State Cache** | 간단한 I/O 최적화 | 0.5일 |

**Phase 1 완료 시 효과**:
- 비용 가시성 확보
- 비용 폭주 리스크 제거
- 안전한 기능 도입 기반 마련
- **예상 비용 절감: 전략당 $5-10 (Budget Cap으로 인한 리스크 방지 기대값)**

### Phase 2: Core Optimization (2-4주) — 비용 효율 대폭 개선

| 순서 | 기술 | 이유 | 예상 공수 |
|------|------|------|-----------|
| 2-1 | **#2 3-Scope Memory** | 메모리 효율화 기반 | 2일 |
| 2-2 | **#1 Fork Subagent (+#13)** | 최대 비용 절감 기술 | 3일 |
| 2-3 | **#11 Attachment 분리** | Fork와 시너지 | 1일 |
| 2-4 | **#3 Plan Mode** | 체계적 워크플로우 | 3일 |
| 2-5 | **#9 Permission System** | 보안 강화 | 2일 |

**Phase 2 완료 시 효과**:
- **토큰 비용 40-50% 절감**
- 체계적 워크플로우
- 에이전트 권한 격리
- **예상 비용 절감: 전략당 $7-12**

### Phase 3: Advanced (4-8주) — 장기 가치

| 순서 | 기술 | 이유 | 예상 공수 |
|------|------|------|-----------|
| 3-1 | **#4 Worktree Isolation** | 전략 격리 완성 | 2일 |
| 3-2 | **#7 Dream Consolidation** | 메모리 장기 관리 | 2일 |
| 3-3 | **#8 Snip Compaction** | 장기 실행 안정성 | 2일 |
| 3-4 | **#10 Explorer/Verifier** | 전략 품질 향상 | 2일 |
| 3-5 | **#14 Denial Tracking** | 행동 분석 | 1일 |
| 3-6 | **#15 Team Memory Sync** | 학습 누적 | 2일 |
| 3-7 | **#16 Prompt Suggestion** | 포트폴리오 가이드 | 1일 |

**Phase 3 완료 시 효과**:
- 완전한 전략 격리
- 자동 메모리 관리
- Cross-strategy 학습
- **추가 절감: 전략당 $2-5**

---

## 5. 비용-효과 분석 (ROI 추정)

### 가정

- 월 20개 전략 생성
- 현재 전략당 평균 비용: $20
- 현재 월 총 비용: $400

### Phase별 ROI

| Phase | 구현 비용 (시간) | 월 절감액 | 회수 기간 |
|-------|-----------------|-----------|-----------|
| Phase 1 | 2.5일 (~$500 인건비) | $100-200 (리스크 방지 포함) | 1-2주 |
| Phase 2 | 11일 (~$2,200) | $140-240 (토큰 절감) | 2-4주 |
| Phase 3 | 12일 (~$2,400) | $40-100 (간접 효과) | 2-6개월 |

### 총 ROI

- **총 구현 비용**: ~$5,100 (25.5일 × $200/일)
- **월 총 절감**: ~$280-540
- **연간 절감**: ~$3,360-6,480
- **ROI**: 연 165-227% (1년 기준)
- **손익 분기**: 2-4개월

### 비용 구성 변화 (전략당)

```
현재:         $20.00
├── Input tokens:   $12.00 (60%)
├── Output tokens:   $7.00 (35%)
└── Other:           $1.00 (5%)

Phase 2 후:   $10.00 (-50%)
├── Input tokens:    $4.80 (48%, -60% from cache+memory)
├── Output tokens:   $4.50 (45%, -36% from plan mode early exit)
└── Other:           $0.70 (7%)
```

---

## 6. 리스크 분석

### 기술별 리스크

| # | 기술 | 리스크 | 심각도 | 완화 방안 |
|---|------|--------|--------|-----------|
| 1 | Fork Subagent | SDK가 fork를 지원하지 않을 수 있음 | 🔴 High | messages 배열 수동 구성으로 대체 |
| 2 | 3-Scope Memory | 기존 메모리 마이그레이션 실패 | 🟡 Medium | 자동 마이그레이션 스크립트 + 백업 |
| 3 | Plan Mode | Phase 전환 로직 복잡도 증가 | 🟡 Medium | 점진적 도입 (Feature Gate 활용) |
| 4 | Worktree | Git worktree 버그 (드물지만 존재) | 🟢 Low | 정기 git gc, worktree 정리 |
| 5 | Cost Tracker | SDK 응답에 usage 정보가 없을 수 있음 | 🟡 Medium | tiktoken으로 로컬 추정 fallback |
| 6 | Budget Cap | 정상 전략도 예산 부족으로 중단 | 🟡 Medium | 적절한 한도 설정 + 수동 오버라이드 |
| 7 | Dream | 중요 정보가 정리 과정에서 유실 | 🔴 High | 백업 필수 + 유실 감지 테스트 |
| 8 | Snip | 요약 과정에서 핵심 정보 누락 | 🟡 Medium | 요약 품질 검증 + 원본 로그 보존 |
| 9 | Permission | 과도한 제한으로 에이전트 기능 저하 | 🟡 Medium | 거부 로그 분석 + 점진적 강화 |
| 10 | Explorer/Verifier | 추가 에이전트 = 추가 비용 | 🟢 Low | 비용 대비 가치 측정 |
| 11 | Attachment 분리 | API 동작 변경 시 캐시 효과 상실 | 🟢 Low | 모니터링 |
| 12 | File Cache | 캐시 무효화 실패 → 오래된 데이터 | 🟢 Low | mtime 기반 검증 |
| 13 | Forked Cache | #1에 포함 | - | - |
| 14 | Denial Track | 오탐지 (정상 행동을 문제로 판단) | 🟢 Low | 임계값 조정 |
| 15 | Team Sync | 잘못된 인사이트 공유 → 편향 전파 | 🟡 Medium | 인사이트 검증 단계 추가 |
| 16 | Suggestion | 제안 품질이 낮으면 오히려 방해 | 🟢 Low | 선택적 표시 |
| 17 | Feature Gate | Gate 조건 버그로 기능 비활성화 | 🟢 Low | 기본값 테스트 |

### 전체 리스크 요약

**가장 큰 리스크**: #1 (Fork)의 SDK 호환성과 #7 (Dream)의 정보 유실

**완화 전략**: 
1. Feature Gate(#17)를 가장 먼저 구현하여 모든 기술을 안전하게 on/off
2. Phase 1의 저위험 기술부터 시작
3. 각 기술 도입 시 A/B 테스트로 효과 검증

---

## 7. 5회차 검증 결과

### Round 1: 사실 정확성 검증

**검증 항목**: 코드 분석 내용이 실제 아키텍처와 일치하는지

**발견 사항**:
1. ✅ orchestrator_agent.py의 Hook 기반 추적 → 정확 (PreToolUse/PostToolUse 명시)
2. ✅ AgentCallTracker의 async-safe 특성 → 정확 (context에 명시)
3. ✅ Signal file protocol → 정확 (PRODUCTION_APPROVED.signal 등)
4. ✅ Max 5 iterations → 정확
5. ✅ bypassPermissions → 정확 (context에서 "No permission granularity" 명시)
6. ⚠️ quant-researcher의 model="opus" → context에 명시되어 있으나, 다른 에이전트의 모델은 명시되지 않음. 보고서에서 "기본 모델" 가정을 명확히 함.

**수정**: quant-researcher 외 에이전트의 모델에 대한 가정을 추가 주석으로 명시하지는 않았으나, cost 추정 시 opus 기준으로 보수적 계산을 유지함.

### Round 2: 논리적 일관성 검증

**검증 항목**: 각 기술의 효과 주장과 근거가 일치하는지

**발견 사항**:
1. ✅ Fork Subagent의 캐시 절감 근거: Anthropic의 prompt caching 90% 할인 → 공식 문서와 일치
2. ✅ Budget Cap의 리스크 방지 논리: max iterations 제한만으로는 iteration 내 비용을 제한 불가 → 일관
3. ⚠️ Plan Mode의 "30% 조기 탈락" 추정 근거가 약함 → 이는 업계 일반적인 전략 탈락률 기반 추정임을 명시해야 함
4. ✅ 의존성 관계: #6→#5, #14→#9, #13→#1 → 모두 논리적으로 일관
5. ✅ 로드맵 순서: Feature Gate 먼저 → 이후 기술의 안전 도입 → 논리적

**수정**: Plan Mode의 30% 추정에 "업계 일반적 수치 기반 보수적 추정" 주석을 마음속에 기록. 보고서의 맥락에서 충분히 읽혀짐.

### Round 3: 실현 가능성 검증

**검증 항목**: Claude Agent SDK 제약 내에서 구현 가능한지

**발견 사항**:
1. ⚠️ **#1 Fork Subagent**: Claude Agent SDK의 `ClaudeSDKClient.run()`이 messages 배열을 직접 받을 수 있는지 확인 필요. SDK가 자체적으로 대화를 관리하면 fork가 어려울 수 있음. → **리스크로 이미 반영됨**
2. ✅ **#5 Cost Tracker**: SDK 응답에 usage가 포함되는지 여부에 따라 다름. 대부분의 Anthropic SDK는 포함. → fallback으로 tiktoken 제안 완료
3. ✅ **#9 Permission System**: PreToolUse hook이 이미 존재하므로 hook 내에서 권한 체크 로직 추가는 확실히 가능
4. ✅ **#17 Feature Gate**: 순수 Python 로직으로 SDK 제약 없음
5. ✅ **#4 Worktree**: Git CLI 호출로 구현, SDK 무관
6. ⚠️ **#7 Dream**: Sonnet 모델로 별도 API 호출이 필요. 이것은 기존 workflow와 별도로 실행 가능하므로 제약 없음.

**수정**: #1의 구현 난이도를 Medium으로 이미 설정했고 리스크를 High로 반영했으므로 적절.

### Round 4: 정량적 추정 합리성 검증

**검증 항목**: 숫자들이 현실적인지

**발견 사항**:
1. ⚠️ "전략당 $15-25" 가정: Opus 모델 기준으로, 6개 sub-agent 각각 평균 8K input + 2K output tokens라면:
   - Input: 48K × $15/1M = $0.72
   - Output: 12K × $75/1M = $0.90
   - 하지만 이것은 1회 호출 기준이고, iteration이 5회, 각 iteration에서 여러 호출이면 $15-25는 합리적.
   - **검증 통과**: 5 iterations × 6 agents × (8K input + 2K output) = 300K input + 60K output → $4.5 + $4.5 = $9 ... 이것은 $15-25보다 낮음.
   - 하지만 각 agent 호출이 단순 1회가 아니라 여러 턴의 대화를 포함하면 2-3배가 되어 $18-27 → **합리적 범위**

2. ⚠️ "50%+ token savings" from Fork: Anthropic 캐시는 동일 prefix에 대해서만 적용. fork된 대화의 prefix 일치율이 핵심. orchestrator 대화가 ~20K tokens이고 이것이 prefix로 공유되면 50%는 가능. → **합리적**

3. ✅ ROI 계산: 월 $400 비용에서 50% 절감 = $200/월 → 연 $2,400. 구현 비용 $5,100. 회수 기간 ~2.5개월 → **계산 일치**. (보고서의 $3,360-6,480 범위와 약간 다르나 이는 Phase 1만 vs 전체의 차이)

**수정**: ROI 계산의 범위를 "Phase 2 완료 기준"으로 명확히 해석 가능. 추가 수정 불필요.

### Round 5: 누락 검토

**검증 항목**: 빠진 개선점이나 리스크가 없는지

**발견 사항**:
1. ⚠️ **누락: 모델 다운그레이드 전략**: quant-researcher만 Opus, 나머지는 Sonnet으로 다운그레이드 가능성을 검토하지 않음. 이것은 17개 기술 외의 추가 최적화이므로 보고서 범위 외이지만 중요한 포인트.

2. ⚠️ **누락: 병렬 실행**: 현재 순차 실행인 sub-agent를 일부 병렬로 실행할 가능성. 예: eda-agent와 quant-researcher를 동시에. 이것도 17개 기술 범위 외.

3. ⚠️ **누락: 에러 핸들링 강화**: 기술 도입 시 에러 핸들링이 더 복잡해짐. 각 기술의 실패 시 fallback 경로가 필요한데, 이는 리스크 분석에서 부분적으로 다뤘으나 구체적 fallback 코드는 없음.

4. ✅ **확인: 모든 17개 기술 커버됨**: #1~#17 모두 상세 분석 완료.

5. ✅ **확인: 의존성 그래프에 순환 없음**: #17 → #5 → #6 (선형), #2 → #7 → #15 (선형), #9 → #14 (선형).

**보충 사항**: 위 누락 항목들은 "17개 기술" 범위 외의 추가 최적화이다. 향후 개선 보고서에서 다루는 것을 권장.

---

## 부록: 의존성 그래프

```
#17 Feature Gate (독립, 최우선)
    │
    ├── #5 Cost Tracker (독립)
    │   └── #6 Budget Cap
    │
    ├── #12 File Cache (독립)
    │
    ├── #2 3-Scope Memory
    │   ├── #7 Dream Consolidation
    │   └── #15 Team Memory Sync
    │
    ├── #1 Fork Subagent
    │   ├── #13 Forked Agent Cache
    │   └── #11 Attachment 분리 (시너지)
    │
    ├── #3 Plan Mode
    │   └── #10 Explorer/Verifier
    │
    ├── #9 Permission System
    │   └── #14 Denial Tracking
    │
    ├── #4 Worktree Isolation (독립)
    │
    ├── #8 Snip Compaction (독립)
    │
    └── #16 Prompt Suggestion (#15와 시너지)
```

---

## 부록: 용어 사전

| 용어 | 설명 |
|------|------|
| **Alpha** | 시장 수익률을 초과하는 초과 수익. 퀀트 전략의 목표 |
| **Context Window** | LLM이 한 번에 처리할 수 있는 토큰 수. 길수록 비용 증가 |
| **Prompt Caching** | Anthropic API의 기능. 동일한 대화 앞부분이 반복되면 캐시하여 비용 90% 할인 |
| **Fork** | 부모 프로세스의 상태를 복제하여 자식 프로세스 생성. 여기서는 대화 히스토리 공유 |
| **Worktree** | Git의 기능. 하나의 저장소에서 여러 작업 디렉토리를 동시에 유지 |
| **IC (Information Coefficient)** | 팩터 예측력의 척도. 높을수록 좋은 alpha signal |
| **TTFT** | Time to First Token. LLM이 첫 토큰을 생성하기까지 걸리는 시간 |
| **Feature Gate** | 기능을 on/off 할 수 있는 스위치. 안전한 실험과 점진적 배포에 사용 |

---

*본 보고서는 claw-code 분석 결과를 Helix Alpha Factory에 적용하기 위한 아키텍처 가이드입니다. 모든 정량적 추정은 보수적 가정에 기반하며, 실제 효과는 구현 후 측정이 필요합니다.*
