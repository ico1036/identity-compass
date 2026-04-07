#!/bin/bash
# 전략팀 실행 명령어
# 주인님이 터미널에서 실행하세요

cd /Users/ryan/.openclaw/workspace/strategy/strategy_2026-04-05_1117

# Claude Code headless 실행
claude -p \"""
당신은 전략팀입니다. 복잡한 시스템 설계를 담당합니다.

작업: asset_attention의 inner loop (Explorer + Critic 자율 시스템)을 재설계하세요.

참고 파일:
- brief/brief.md — 작업 요청서
- context/program.md — 현재 프로그램 구조
- context/critic.md — Critic 페르소나
- context/philosophy.md — THE MISSION
- context/insights.md — 현재 실험 상황
- context/review_r7_*.md — Critic 리뷰

요구 산출물 (output/ 디렉토리에 작성):
1. run_inner_loop.sh — 메인 오케스트레이터
2. explorer_task.md — Explorer용 프롬프트
3. critic_task.md — Critic용 프롬프트
4. cron_setup.md — 로컬 cron 설정 가이드
5. (선택) telegram_notify.py — 결과 요약 스크립트

핵심 원칙:
- OpenClaw 없이 로컬 cron만으로 동작
- Claude Code headless (claude -p) 사용
- 파일 기반 상태머신 (LOCK, NEEDS_CRITIC)
- 6시간+ stale LOCK 자동 정리
- git commit/push 포함

작업 완료 후 output/에 모든 파일 작성하고 종료하세요.
""" \
--output-dir output/ \
--allowed-tools "Bash,Read,Write,Edit" \
--timeout 1800000

echo "전략팀 작업 완료"
ls -la output/
