# 전략팀 (Strategy Team) — 복잡 설계 전담

복잡한 아키텍처 설계, 프로토콜 재설계, 대규모 리팩토링을 Claude Code headless에 위임하는 스킬.

## When to Use

사용 시점: 복잡도가 Kimi의 처리 한계를 넘어갈 때

| 복잡도 | 예시 | 처리자 |
|--------|------|--------|
| 낮음 | 상태 확인, 커밋, 간단한 파일 수정 | Kimi (즉시) |
| 중간 | 실험 결과 분석, 다음 단계 제안 | Kimi (대화) |
| **높음** | **새 attention 아키텍처 설계, 전체 프로토콜 재설계, 논문 작성** | **전략팀 (Claude Code)** |

## Workflow

```
주인님: "attention 구조 문제 있는 것 같은데 새로 짜줘"
    ↓
Kimi: 복잡도 판단 → "전략팀 소환 필요"
    ↓
전략팀 스킬 실행
    ↓
1. 작업 패키지 생성 (strategy_package_YYYYMMDD_HHMMSS/)
2. Claude Code headless 실행 스크립트 생성
3. 주인님께 실행 명령어 제공
    ↓
주인님: 터미널에서 명령어 실행 (또는 Kimi가 로컬 cron 등록)
    ↓
Claude Code: 작업 수행 → 결과물을 패키지에 저장
    ↓
Kimi: 결과물 요약 → 주인님께 보고
```

## Strategy Package Structure

```
workspace/strategy/
└── strategy_2026-04-05_111600/
    ├── brief.md              # 작업 요청서 (Kimi가 작성)
    ├── context/              # 참고 자료
    │   ├── current_train.py
    │   ├── latest_review.md
    │   └── insights.md
    ├── output/               # Claude Code 산출물
    │   ├── design.md
    │   ├── new_train.py
    │   └── implementation_notes.md
    └── summary.md            # Kimi가 작성한 요약
```

## Usage Examples

### 1. 아키텍처 재설계
```
주인님: "attention이 안 먹히는데 구조를 완전히 바꿔야 할 것 같아"

Kimi: 전략팀 소환
→ brief.md: "현재 CrossAttentionAllocator 217 params, regime signal 0. 
   새로운 temporal attention 아키텍처 3가지 설계 필요."
→ Claude Code가 3 variant 설계
→ Kimi가 결과 요약
```

### 2. 실험 프로토콜 재설계
```
주인님: "17실험 했는데 regime signal이 0이야. training protocol이 문제일 수도?"

Kimi: 전략팀 소환
→ brief.md: "Expanding window + cold start 문제. 
   Warm-start, minimum window, sliding window 등 대안 설계"
→ Claude Code가 새로운 protocol.py 작성
```

### 3. 논문/보고서 작성
```
주인님: "asset_attention 결과를 논문으로 쓰고 싶어"

Kimi: 전략팀 소환
→ brief.md: "17 experiment results, regime learning failure analysis"
→ Claude Code가 arXiv format draft 작성
```

## How It Works

### Phase 1: Package Creation (Kimi)
1. 작업 복잡도 평가
2. 필요한 context 수집 (current code, reviews, insights)
3. brief.md 작성 (명확한 요구사항)
4. 실행 스크립트 생성

### Phase 2: Execution (Claude Code)
1. 주인님이 터미널에서 실행
2. Claude Code가 headless로 작업
3. 결과물을 output/에 저장
4. 완료 시그널 (DONE 파일 생성)

### Phase 3: Summary (Kimi)
1. output/ 내용 읽기
2. 주요 변경사항 요약
3. 주인님께 보고
4. asset_attention/에 적용할지 결정

## Complexity Checklist

아래 중 하나라도 해당되면 전략팀 소환:
- [ ] 새로운 알고리즘/아키텍처 설계 필요
- [ ] 기존 코드 100줄 이상 변경
- [ ] 새로운 파일 3개 이상 생성
- [ ] 학술적 글쓰기 (논문, 리포트)
- [ ] 복잡한 프로토콜 설계 (상태머신, 파이프라인)

## Commands

### 소환
```
주인님: "전략팀 불러" 또는 "이건 복잡하니까 전략팀에게" 등
```

### 패키지 생성
Kimi가 자동으로 `workspace/strategy/strategy_YYYYMMDD_HHMMSS/` 생성

### 실행
```bash
# 주인님이 터미널에서
cd workspace/strategy/strategy_2026-04-05_111600
claude -p "Follow brief.md instructions. Write all outputs to output/ directory."
```

### 결과 확인
```
주인님: "전략팀 결과 봐줘"

Kimi: output/ 읽고 요약 보고
```

## Integration with asset_attention

전략팀 결과물 적용 흐름:
1. output/new_train.py → Kimi가 검토
2. 주인님 승인 → asset_attention/train.py로 복사
3. git commit
4. 새로운 실험 시작 (Explorer 또는 수동)

## Safety Rules

- 전략팀은 **절대** asset_attention/를 직접 수정하지 않음
- 항상 workspace/strategy/에 격리된 패키지로 작업
- 주인님 승인 후에만 결과물을 asset_attention/에 적용
- Kimi가 중간 검증 (미션 위반 여부, guard.py 호환성 등)

## Current Status

대기 중. 다음 작업 대기:
- [ ] Exp 0017-0021 설계 검증 (warm-start, MDD 조사)
- [ ] 새로운 attention 아키텍처 (H2 pivot 준비)
- [ ] 논문 초안 (선택)
