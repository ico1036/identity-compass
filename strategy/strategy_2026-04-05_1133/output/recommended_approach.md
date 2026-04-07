# Recommended Approach: Agent SDK While Loop with Safeguards

## Decision

**Agent SDK While Loop**를 채택합니다.

**핵심 근거:**
1. **적정 기술** - Ralph는 산업용 스케일(1000 alphas/day), 우리는 학술용(50-100 experiments)
2. **직접 제어** - attention 실패 원인 파악에 단순한 코드가 유리
3. **확장 가능** - 나중에 Ralph로 마이그레이션은 쉬움, 반대는 어려움

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Main Daemon (Claude Code Session)           │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Safeguard Layer                         │   │
│  │  - Cost tracker ($20/batch limit)               │   │
│  │  - Memory monitor (restart every 5 batches)     │   │
│  │  - STOP signal checker                          │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Loop Orchestrator                       │   │
│  │                                                 │   │
│  │  while running:                                 │   │
│  │    ├─▶ spawn_subagent(Explorer)                 │   │
│  │    │   └── 5 experiments                        │   │
│  │    │   └── git commit                           │   │
│  │    │   └── create NEEDS_CRITIC                  │   │
│  │    │                                           │   │
│  │    ├─▶ spawn_subagent(Critic)                  │   │
│  │    │   └── review latest cards                 │   │
│  │    │   └── write verdict (PASS/REVISE/FAIL)    │   │
│  │    │   └── remove NEEDS_CRITIC                 │   │
│  │    │                                           │   │
│  │    └─▶ if verdict == FAIL: break               │   │
│  │        if verdict == REVISE: continue          │   │
│  │        if verdict == PASS: next batch          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Human Interface                         │   │
│  │  - STOP file (즉시 중단)                         │   │
│  │  - Telegram notifications (선택)                │   │
│  │  - Status checkpoint files                      │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│              Minimal Watchdog (launchd)                  │
│  - Main daemon 죽었는지 1시간마다 체크                    │
│  - 죽었으면 재시작 (optional, cron 아님)                  │
└─────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Core Loop (즉시 구현)
- `main_daemon.py` - While loop + subagent spawning
- `explorer_prompt_v2.md` - Explorer용 프롬프트
- `critic_prompt_v2.md` - Critic용 프롬프트
- `safeguards.py` - Cost/memory monitoring

### Phase 2: Human Interface (1-2일 내)
- STOP 파일 처리
- 상태 체크포인트 (BATCH_05_COMPLETE 등)
- 간단한 로그 파일

### Phase 3: Optional Enhancements (나중에)
- Telegram 알림
- launchd watchdog
- Web dashboard

## Key Design Decisions

### 1. Subagent vs Direct Execution
**결정:** spawn_subagent 사용

**이유:**
- 격리 - Explorer 실패가 daemon 전체를 죽이지 않음
- 리소스 정리 - subagent 종료 시 메모리 반환
- 재시작 가능 - 문제 있으면 새로 스폰

### 2. Session Lifetime
**결정:** 5 batches마다 daemon 재시작

**이유:**
- 메모리 누수 방지
- Cost tracking 리셋 (명확한 구획)
- 주인님 개입 포인트

### 3. State Management
**결정:** 파일 기반 (LOCK, NEEDS_CRITIC, checkpoint files)

**이유:**
- daemon 죽어도 상태 보존
- git에 tracking 가능
- 간단하고 디버깅 용이

### 4. Cost Control
**결정:** $20/batch (약 5 experiments = 1 batch)

**계산:**
- Explorer: ~$2-3/experiment × 5 = $10-15
- Critic: ~$3-5/review
- Total/batch: ~$15-20
- 20 batches = ~$300-400 (석사 논문 수준 적정)

## File Structure

```
asset_attention/
├── daemon/
│   ├── main_daemon.py
│   ├── safeguards.py
│   └── prompts/
│       ├── explorer_v2.md
│       └── critic_v2.md
├── loop_control/
│   ├── STOP
│   ├── PAUSE
│   ├── checkpoint_*.json
│   └── cost_log.json
└── ... (기존 구조)
```

## Running the Loop

```bash
# 1. 시작
python daemon/main_daemon.py

# 2. 중단 (새 터미널에서)
touch asset_attention/loop_control/STOP

# 3. 상태 확인
cat asset_attention/loop_control/cost_log.json
cat asset_attention/loop_control/checkpoint_*.json

# 4. 5배치 완료 후 자동 재시작
# 또는 수동 재시작
rm asset_attention/loop_control/STOP
python daemon/main_daemon.py
```

## Monitoring

```bash
# 실시간 로그
 tail -f asset_attention/loop_control/daemon.log

# 비용 확인
python -c "import json; d=json.load(open('loop_control/cost_log.json')); print(f\"Total: ${d['total']:.2f}\")"

# 현재 상태
cat asset_attention/loop_control/checkpoint_latest.json
```

## Failure Modes & Recovery

| 시나리오 | 감지 | 복구 |
|----------|------|------|
| Explorer hang | 30분 타임아웃 | kill, log error, retry |
| Critic reject | verdict=FAIL | notify human, stop |
| Cost limit | $20/batch 초과 | graceful stop, notify |
| Memory pressure | 80% RAM | restart daemon |
| Code error | exception | log, skip batch, continue |
| Network fail | API error | exponential backoff |

## Migration from Current System

1. 현재 asset_attention/ 구조는 그대로 유지
2. daemon/ 디렉토리 신규 추가
3. 기존 docs/program.md는 참고용으로 보존
4. 새로운 loop는 daemon/에서 실행
5. cards/, docs/reviews/는 공유

## Next Steps

1. ✅ 이 문서 승인
2. main_daemon.py 구현
3. safeguards.py 구현
4. 프롬프트 v2 작성
5. 첫 배치 테스트
6. launchd watchdog (선택)
