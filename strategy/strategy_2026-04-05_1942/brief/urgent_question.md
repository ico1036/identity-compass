# 전략팀 긴급 질의: Ralph 실행 메커니즘

## 상황

**사용자 환경:**
- Claude Code 계정에 Ralph 플러그인 설치됨
- 실행 방법 불명확
- 현재 cron 기반 시스템은 작동 중 (최근 실험 0031-0034 완료, regime signal 발견)

**질문:**

1. **Claude Code에서 Ralph 플러그인 실행 방법**
   - 옵션 A: `/ralph asset_attention` (슬래시 커맨드)
   - 옵션 B: `claude /ralph asset_attention` (터미널)
   - 옵션 C: `claude -p "run ralph loop"` (프롬프트)
   - 옵션 D: Claude Code 난독 설정 파일 (JSON/YAML)

2. **현재 상황 판단**
   - cron이 실제로 작동 중 (Exp 0031-0034 완료)
   - Regime signal 발견 (11-13% shift)
   - Ralph 마이그레이션 필요한가, 아니면 현재 유지?

3. **권장 실행 방식**
   - 사용자가 "claudecode 계정에 플러그인으로 깔려있다"고 함
   - 정확한 실행 명령어는?

## 요구 답변

간단한 답변:
- 실행 명령어 (정확한 syntax)
- 현재 상황에서의 권장 (마이그레이션 vs 유지)
