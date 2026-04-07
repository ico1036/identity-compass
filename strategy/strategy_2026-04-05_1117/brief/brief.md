# 전략팀 작업 요청서: Inner Loop 재설계

## 현재 상황 (AS-IS)

**구조:**
- cron (15분마다) → isolated 세션 생성 → Explorer 또는 Critic 실행
- Explorer: 5실험 → NEEDS_CRITIC 생성 → 종료
- Critic: 리뷰 작성 → NEEDS_CRITIC 삭제 → 종료
- 반복

**문제:**
1. OpenClaw Claude OAuth 금지 → API 401 에러
2. cron이 세션 생성 실패
3. LOCK stale (6시간+) → 루프 멈춤
4. 17실험 했으나 regime signal 0 → Critic FAIL 판정

**실험 결과:**
- 17 experiments (Exp 0000-0016)
- Best: iTransformerAllocator (249 params) test_sharpe 0.931
- Regime signal: 0.000 (전무)
- EW benchmark: 1.39 (모든 attention 모델이 열위)
- Critic 판정: H2 (Attention 잘못된 접근) 확률 70%

## 목표 (TO-BE)

**핵심 요구:** Claude Code headless 기반 자율 루프

1. **탈-OpenClaw**: cron은 로컬(Mac Mini)에서 직접 실행
2. **Claude Code 직접 호출**: `claude -p`로 headless 실행
3. **상태 기반 자동화**: 파일 기반 상태머신 (LOCK, NEEDS_CRITIC, READY_FOR_NEXT)
4. **견고한 에러 처리**: 6시간+ stale LOCK 자동 정리
5. **결과 리포팅**: Telegram으로 간단한 요약 전송 (선택)

## 요구 산출물

1. `run_inner_loop.sh` — 메인 오케스트레이터 스크립트
2. `explorer_task.md` — Explorer 프롬프트 (Claude Code용)
3. `critic_task.md` — Critic 프롬프트 (Claude Code용)
4. `cron_setup.md` — 로컬 cron 설정 가이드
5. `telegram_notify.py` — 간단한 결과 요약 스크립트 (선택)

## 핵심 설계 질문

1. cron이 15분마다 `run_inner_loop.sh`를 실행하는가?
2. 스크립트가 LOCK 파일을 확인하고 stale이면 정리하는가?
3. NEEDS_CRITIC 있으면 Critic 태스크를 실행하는가?
4. 없으면 Explorer 태스크를 실행하는가?
5. 각 태스크가 완료 후 다음 상태 파일을 생성하는가?
6. 에러 발생 시 로그를 남기고 graceful하게 종료하는가?

## 제약조건

- Mac Mini M4, 32GB RAM
- Claude Code CLI 이미 설치됨
- Python 3.11+, uv 사용
- asset_attention/ 리포지토리 구조 유지
- git commit/push 필수

## 참고 자료

- context/ 디렉토리에 현재 코드, 리뷰, insights 첨부
