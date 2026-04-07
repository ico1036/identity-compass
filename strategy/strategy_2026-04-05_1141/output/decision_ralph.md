# 재검토 결과: Ralph Plugin 선정

## 변경된 전제
| 항목 | 이전 | 현재 |
|------|------|------|
| 비용 | $20 제한 | unlimited |
| Ralph 상태 | 없음 | 이미 플러그인 존재 |
| 목표 | 최적의 구조 | 코드 최소화 |

## 결론: Ralph Plugin

**SDK While 문제:**
- main_daemon.py 직접 작성 (150줄+)
- safeguards.py 직접 작성 (100줄+)
- 세션 관리, 리스타트, 에러 처리 직접 구현
- 총 500줄+

**Ralph Plugin 해결:**
- Ralph가 루프 관리 (이미 있음)
- Ralph가 서브에이전트 관리 (이미 있음)
- 우리는 stop_hook만 추가 (10줄)
- 프롬프트 2개만 작성 (md 파일)
- 총 100줄 내외

## 구현 내용

```python
# ralph_plugin_asset_attention.py (20줄)
from ralph import Loop, StopHook
from pathlib import Path

class AssetAttentionLoop(Loop):
    def check_stop(self):
        return StopHook.INTERRUPT if Path("STOP").exists() else StopHook.CONTINUE
```

```markdown
# prompts/explorer_v2.md (기존과 동일)
# prompts/critic_v2.md (기존과 동일)
```

## 실행
```bash
ralph run asset_attention --explorer-prompt v2 --critic-prompt v2
```

Ralph로 결정하겠습니다.
