# 전략팀 작업 요청서 v4: Ralph Plugin 구현

## 결정된 사항
- **방식**: Ralph Plugin (SDK While 대신)
- **이유**: 이미 Ralph 인프라 존재, 코드 최소화
- **비용**: unlimited (제약 없음)

## 요구 산출물

실제 동작하는 코드와 설정 파일:

1. **ralph_plugin.py** — AssetAttentionLoop 클래스 (20줄 내외)
   - StopHook: STOP 파일 체크
   - Ralph의 Explorer/Critic 사용

2. **explorer_v2.md** — Explorer 프롬프트
   - 5실험 수행
   - Exit Protocol (NEEDS_CRITIC 생성)
   - Git commit/push

3. **critic_v2.md** — Critic 프롬프트
   - 최근 5실험 리뷰
   - Verdict: PASS/REVISE/FAIL
   - insights.md 업데이트

4. **run.sh** — 실행 스크립트
   - Ralph 플러그인 로드
   - 루프 시작

5. **setup.md** — 설치 가이드
   - Ralph에 플러그인 등록
   - 프롬프트 경로 설정

## Ralph 가정

Ralph가 이미 설치되어 있고 다음을 제공한다고 가정:
- `ralph.Loop` — 기본 루프 클래스
- `ralph.StopHook` — 중단 훅
- `ralph.Explorer` — Explorer 에이전트
- `ralph.Critic` — Critic 에이전트
- `ralph.run()` — 루프 실행

## 파일 구조

```
workspace/asset_attention/
├── ralph_plugin.py          # 산출물 1
├── prompts/
│   ├── explorer_v2.md       # 산출물 2
│   └── critic_v2.md         # 산출물 3
├── run.sh                   # 산출물 4
└── SETUP.md                 # 산출물 5
```

## 실행 목표

```bash
cd /Users/ryan/.openclaw/workspace/asset_attention
./run.sh
# → Ralph가 Explorer 5실험 → Critic 리뷰 → 반복
```

## 중단 방법

```bash
touch STOP  # Ralph가 체크해서 graceful stop
```
