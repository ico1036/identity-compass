#!/bin/bash
# strategy_runner_v2.sh - Cron-less Loop Architecture

cd /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1133

echo "=== 전략팀 v2: Cron-less Loop Architecture ==="
echo ""
echo "작업: Ralph Loop Plugin vs Agent SDK While Loop 비교 및 설계"
echo ""

# Check if claude is available
if ! command -v claude &> /dev/null; then
    echo "❌ Claude Code not found. Please install: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

echo "✓ Claude Code found"
echo ""
echo "참고 파일:"
ls -la brief/ context/
echo ""
echo "Claude Code 실행 중... (예상 10-20분)"
echo ""

# Run Claude Code with the brief
claude -p "당신은 전략팀입니다. 자율 AI 연구 시스템의 loop 구조를 설계해야 합니다.

**과제**: cron 없이 작동하는 inner loop 구조를 설계하세요.

**두 가지 접근법 비교**:
1. Ralph Loop Plugin Approach
2. Agent SDK While Loop Approach

**요구사항**:
- OpenClaw 미사용 (Claude OAuth 금지됨)
- Claude Code subagent/hook/sdk 사용
- 주인님 개입 메커니즘 필수 (STOP 파일 등)
- 비용/메모리 모니터링
- 죽었을 때 복구 방법

**참고 파일 경로**:
- /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1133/brief/brief_v2.md
- /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1133/context/*

**산출물** (output/ 디렉토리에 작성):
1. architecture_comparison.md — 두 접근법 상세 비교
2. recommended_approach.md — 추천 방식 및 근거  
3. implementation_guide.md — 구현 단계별 가이드
4. monitoring_setup.md — 상태 모니터링 및 알림
5. (선택) poc_script.py — proof-of-concept 코드

먼저 brief_v2.md를 읽고, 두 접근법을 분석하여 추천 방식을 결정하세요." \
--allowed-tools "Bash,Read,Write,Edit" 2>&1 | tee output/claude_output.log

echo ""
echo "=== 작업 완료 ==="
echo "산출물:"
ls -la output/
