# 전략팀 작업 요청서 v2: Cron-less Loop Architecture

## 배경
기존 inner loop 재설계에서 cron을 제외하고, Claude Code 난독 구조로 완전한 자율 루프를 만들어야 합니다.

## 현재 상황
- asset_attention: 17실험 완료, regime signal 0, Critic FAIL
- Claude Code: subagent, hook, agent_sdk 사용 가능
- claude_agent_sdk_lab: 이미 로그인되어 있음
- OpenClaw: 연결 끊김 (사용 안 함)

## 선택지 두 가지

### A. Ralph Loop Plugin Approach
**개념**: asset_attention에 ralph loop를 플러그인 형태로 통합

**장점:**
- 기존 ralph infrastructure 활용 (코스트 트래킹, 버짓 캡 등)
- 표준화된 서브에이전트 스폰 메커니즘
- 별도의 while loop 관리 불필요

**단점:**
- ralph loop 의존성 추가
- 커스터마이징 제한
- helix 프로젝트와 결합 시 복잡도 증가

**구현 시 고려:**
```python
# ralph_plugin.py
from claude_agent_sdk import Agent

class AssetAttentionLoop:
    def __init__(self):
        self.explorer = Agent(name="explorer", task=...)
        self.critic = Agent(name="critic", task=...)
    
    def run_batch(self):
        results = self.explorer.run(max_experiments=5)
        verdict = self.critic.review(results)
        return verdict
```

### B. Agent SDK While Loop Approach
**개념**: Claude Code 메인 세션이 while True로 직접 서브에이전트 관리

**장점:**
- 완전한 제어권 (커스터마이징 자유)
- 컨텍스트 공유 용이
- hook으로 실시간 알림 가능
- 간단한 구조

**단점:**
- 메모리 누수 가능성 (장시간 세션)
- 비용 지속 발생
- 죽었을 때 복구 메커니즘 필요

**구현 시 고려:**
```python
# main_loop.py
from claude_agent_sdk import spawn_subagent

while True:
    # Check stop signal
    if os.path.exists("STOP"):
        break
    
    # Explorer
    explorer = spawn_subagent(task="...")
    results = explorer.run()
    
    # Critic
    critic = spawn_subagent(task="...")
    verdict = critic.review(results)
    
    if verdict == "FAIL":
        notify_human()
        break
    elif verdict == "REVISE":
        continue
    # PASS: next batch
```

## 비교 차트

| 항목 | Ralph Plugin | Agent SDK While |
|------|--------------|-----------------|
| 복잡도 | 중간 (ralph 의존) | 낮음 (직접 구현) |
| 유연성 | 제한적 | 높음 |
| 모니터링 | ralph 제공 | 직접 구현 필요 |
| 복구 메커니즘 | ralph 제공 | signal 파일 + 재시작 스크립트 |
| 비용 최적화 | ralph 제공 | 직접 구현 |
| 학습 곡선 | ralph 학습 필요 | SDK 문서만 |

## 핵심 질문

전략팀이 답해야 할 질문:

1. **ralph loop를 asset_attention에 통합하는 것이 현실적인가?**
   - ralph는 helix 용으로 설계됨
   - ETF allocation에 맞는 조정 필요
   - 오버엔지니어링 위험

2. **while loop의 메모리/비용 문제를 어떻게 완화할 수 있는가?**
   - 주기적 세션 재시작?
   - 배치 크기 조정?
   - 비용 모니터링?

3. **"죽었을 때" 복구는 어떻게 할 것인가?**
   - 외부 watchdog (간단한 cron 또는 launchd)
   - signal 파일 체크
   - 재시작 시 상태 복원

4. **주인님이 중간에 개입하려면 어떤 메커니즘이 필요한가?**
   - STOP 파일
   - Telegram 알림 hook
   - 상태 확인 명령어

## 요구 산출물

1. `architecture_comparison.md` — 두 접근법의 상세 비교
2. `recommended_approach.md` — 추천 방식 및 근거
3. `implementation_guide.md` — 구현 단계별 가이드
4. `monitoring_setup.md` — 상태 모니터링 및 알림 설정
5. (선택) `poc_script.py` — 핵심 루프의 proof-of-concept

## 제약조건

- cron 사용 금지 (watchdog 용도로만 최소한 사용 가능)
- Claude Code CLI 또는 Agent SDK 사용
- Mac Mini M4, 32GB RAM
- 주인님 개입 메커니즘 필수
- 비용 모니터링 필수

## 참고 자료

- context/ralph/ (있는 경우)
- context/claude_agent_sdk/ (있는 경우)
- 기존 asset_attention 구조
