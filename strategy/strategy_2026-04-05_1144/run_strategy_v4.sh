#!/bin/bash
# strategy_runner_v4.sh - Ralph Plugin Implementation

cd /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1144

echo "=== 전략팀 v4: Ralph Plugin 구현 ==="
echo ""

# Check claude
if ! command -v claude &> /dev/null; then
    echo "❌ Claude Code not found"
    exit 1
fi

echo "✓ Claude Code found"
echo ""
echo "작업: Ralph Plugin 실제 코드 작성"
echo ""

# Create output directories
mkdir -p output/prompts

# Run Claude Code
claude -p "당신은 전략팀입니다. Ralph Plugin을 실제로 구현해야 합니다.

**과제**: asset_attention용 Ralph Plugin 코드와 프롬프트를 작성하세요.

**참고**: 
- /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1144/brief/brief_v4.md
- /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1144/context/

**산출물** (output/ 디렉토리에 작성):

1. output/ralph_plugin.py — AssetAttentionLoop 클래스
   - StopHook으로 STOP 파일 체크
   - Ralph의 Explorer, Critic 사용

2. output/prompts/explorer_v2.md — Explorer 프롬프트
   - 5실험 수행 (attention-based regime learning)
   - Exit Protocol: NEEDS_CRITIC 생성
   - Git commit/push

3. output/prompts/critic_v2.md — Critic 프롬프트
   - 최근 5실험 리뷰
   - Verdict: PASS/REVISE/FAIL
   - insights.md 업데이트

4. output/run.sh — 실행 스크립트

5. output/SETUP.md — 설치 및 실행 가이드

**Ralph 가정** (이미 설치됨):
- from ralph import Loop, StopHook, Explorer, Critic
- ralph.run()으로 실행

**핵심**: 코드 최소화, Ralph 인프라 최대한 활용" \
--allowed-tools "Bash,Read,Write,Edit" 2>&1 | tee output/claude_output.log

echo ""
echo "=== 작업 완료 ==="
ls -la output/
