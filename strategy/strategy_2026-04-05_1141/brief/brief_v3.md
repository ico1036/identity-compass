# 전략팀 재검토: Ralph Plugin (수정안)

## 배경 변경
- 비용 이슈: **해당없음** (unlimited)
- Ralph: 이미 플러그인/훅 구조 존재
- 목표: **코드 최소화**, 재사용 최대화

## Ralph Plugin 구조 (기존 활용)

```python
# asset_attention_plugin.py
# 이미 존재하는 ralph infrastructure 활용

from ralph import Loop, StopHook, BudgetCap
from ralph.agents import Explorer, Critic

class AssetAttentionLoop(Loop):
    """Ralph 기반 루프 - 최소 코드"""
    
    def __init__(self):
        super().__init__()
        self.explorer = Explorer(
            prompt="explorer_v2",  # md 파일만 교체
            max_experiments=5,
            stop_hook=self.stop_hook
        )
        self.critic = Critic(
            prompt="critic_v2",
            stop_hook=self.stop_hook
        )
    
    def stop_hook(self, signal):
        """STOP 파일 체크"""
        if Path("STOP").exists():
            return StopHook.INTERRUPT
        return StopHook.CONTINUE
    
    def run_batch(self):
        """Ralph가 관리 - 우리는 정의만"""
        # Explorer 5실험
        results = self.explorer.run()
        
        # Critic 리뷰
        verdict = self.critic.review(results)
        
        return verdict

# 실행은 Ralph가 알아서
# main.py
from ralph import run
run(AssetAttentionLoop())
```

## SDK vs Ralph (코드량 비교)

| 항목 | SDK While | Ralph Plugin |
|------|-----------|--------------|
| 메인 루프 | 150줄 직접 작성 | 20줄 (Ralph가 관리) |
| 세이프가드 | 직접 구현 | Ralph 제공 |
| 서브에이전트 | spawn_subagent 직접 | Ralph.Explorer/Critic |
| STOP 처리 | 파일 체크 로직 | stop_hook만 등록 |
| 리스타트 | 직접 구현 | Ralph 제공 |

**Ralph 승리:** 코드 80% 감소

## 새 추천: Ralph Plugin

**근거:**
1. 이미 Ralph 인프라 있음
2. 비용 제약 없음
3. 코드 최소화
4. stop hook만 추가하면 됨

**구현:**
```bash
# 1. ralph에 asset_attention 플러그인 등록 (이미 됐을 수도)
# 2. explorer_v2.md, critic_v2.md만 작성
# 3. stop_hook만 추가
# 4. 실행
```

## 구조

```
ralph/
├── plugins/
│   └── asset_attention.py      # 20줄
├── prompts/
│   ├── explorer_v2.md          # 새로 작성
│   └── critic_v2.md            # 새로 작성
└── hooks/
    └── asset_attention_stop.py # STOP 파일 체크
```

## 차이점

**이전 (SDK):** 
- daemon/, safeguards.py, main_daemon.py 직접 작성
- 500줄+

**새로 (Ralph):**
- ralph 플러그인 1개
- 프롬프트 2개
- 100줄 내외

Ralph로 갈까요?
