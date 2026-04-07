# skill-finder - ClawHub 자동 스킬 발견 및 설치

## Overview

상황에 맞게 ClawHub에서 필요한 스킬을 자동으로 찾아서 설치하는 스킬입니다.

## When to use

- 사용자가 특정 작업을 요청했는데 필요한 스킬이 없을 때
- "~하는 스킬 있어?"라고 물어봤을 때
- 새로운 기능이 필요할 때

## Workflow

1. 사용자 요청 분석 → 필요한 스킬 키워드 추출
2. ClawHub 검색 (web_search 사용)
3. 적절한 스킬 선택
4. 설치 및 적용

## Usage

```
주인님: "이메일 본문 요약해줘"
→ 이메일 관련 스킬이 없으면 자동으로 ClawHub에서 검색
→ 적절한 스킬 설치 제안 또는 자동 설치
```

## Installation

```bash
openclaw skills install <skill-name>
```

## Note

- 설치 전 항상 주인님에게 확인
- 민감한 작업(이메일 발송 등)은 권한 확인 필요
