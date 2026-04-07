---
name: auto-skill-finder
description: Automatically discovers and installs missing skills from ClawHub when users request functionality that requires skills not currently available. Use when users ask for tasks that might need external skills like email handling, calendar management, social media posting, web scraping, database operations, etc. The skill searches ClawHub, finds appropriate matches, and either suggests installation or auto-installs based on user preference.
---

# Auto Skill Finder

## Overview

주인님의 요청을 분석하여 필요한 스킬이 없을 경우, ClawHub에서 자동으로 찾아서 설치해드립니다.

## When to Trigger

- 사용자가 특정 기능을 요청했는데 필요한 스킬이 설치되지 않은 경우
- "~할 수 있는 스킬 있어?"라고 물어봤을 때
- 새로운 통합/자동화 기능이 필요할 때

## Detection Keywords

이러한 키워드가 포함된 요청은 추가 스킬이 필요할 수 있습니다:

| 카테고리 | 키워드 |
|---------|--------|
| 이메일 | email, gmail, outlook, mail, send email, inbox |
| 캘린더 | calendar, schedule, google calendar, outlook calendar, 일정 |
| 뉴스 | news, rss, headlines, 뉴스 |
| SNS | twitter, mastodon, bluesky, tweet, post to, 트윗 |
| 금융 | stock, crypto, bitcoin, trading, 주식, 코인 |
| 날씨 | weather, forecast, 날씨, 예보 |
| 파일처리 | pdf, docx, excel, spreadsheet, 문서 |
| 이미지 | image, photo, ocr, vision, 사진, 이미지 |
| 음성 | audio, voice, tts, podcast, 음성, 목소리 |
| 데이터베이스 | database, db, sqlite, postgres, sql |
| 자동화 | automation, workflow, cron, schedule task |
| Git | git, github, gitlab, commit, push, PR |
| 클라우드 | aws, gcp, azure, s3, ec2, 서버 |
| 홈자동화 | home assistant, smart home, iot, hue, homekit |
| 메시징 | slack, discord, telegram, whatsapp, signal, message |
| 개발도구 | docker, kubernetes, terraform, ci/cd |

## Workflow

### Step 1: 요청 분석

사용자의 요청에서 필요한 스킬 카테고리 감지:

```javascript
// 예시 요청: "내 이메일에서 중요한 메일만 요약해줘"
// → email 카테고리 감지
// → 필요한 스킬: gmail, email-parser, summarizer 등
```

### Step 2: 설치된 스킬 확인

현재 설치된 스킬 목록 확인:

```
- healthcheck ✓
- weather ✓
- coding-agent ✓
- skill-creator ✓
- tmux ✓
- gmail ✗ (없음!)
```

### Step 3: ClawHub 검색

web_search 도구를 사용하여 ClawHub에서 적절한 스킬 검색:

```
쿼리: "gmail skill site:clawhub.ai"
쿼리: "email skill openclaw"
```

### Step 4: 결과 분석 및 제안

검색 결과에서 가장 적절한 스킬 선택 후 주인님에게 제안:

```
주인님, 이메일 처리를 위해 다음 스킬을 발견했습니다:

1. gmail-skill (★★★★★)
   - Gmail API 연동
   - 이메일 읽기/쓰기/삭제
   - 레이블 관리
   
2. email-parser (★★★★☆)
   - 이메일 본문 파싱
   - 첨부파일 처리

설치하시겠습니까? (예/아니오/자동모드)
```

### Step 5: 설치

사용자 승인 시 스킬 설치:

```bash
# 스킬 설치 명령
openclaw skills install <skill-name>
```

## Auto-Install Mode

주인님이 "자동모드"를 설정하면, 다음과 같이 작동합니다:

1. 신뢰할 수 있는 스킬 자동 설치
2. 민감한 권한 필요 시에만 확인 (이메일 발송, 소셜 포스팅 등)
3. 설치 완료 후 바로 작업 수행

## Safety Rules

- **자동 설치 전**: 스킬 설명과 리뷰 확인
- **민감 작업**: 항상 주인님 확인 (이메일 발송, 돈 관련, 공개 포스팅)
- **권한 요청**: API 키, OAuth 등 필요 시 안내
- **롤백**: 설치 실패 시 이전 상태 복구

## Example Usage

### Scenario 1: 이메일 요약 요청

**주인님**: "내 Gmail에서 오늘 온 중요한 이메일 요약해줘"

**처리 과정**:
1. → gmail 스킬 필요 감지
2. → 설치된 스킬 확인 (없음)
3. → ClawHub 검색: "gmail skill clawhub"
4. → 발견: gmail-skill, email-parser
5. → 주인님 제안: "Gmail 연동 스킬을 설치하시겠습니까?"
6. → 설치 후 작업 수행

### Scenario 2: 트윗 포스팅

**주인님**: "이 내용을 Twitter에 올려줘"

**처리 과정**:
1. → twitter/social 스킬 필요 감지
2. → ClawHub 검색: "twitter skill clawhub"
3. → 발견: twitter-skill, social-poster
4. → ⚠️ 민감 작업 확인: "Twitter에 포스팅하시겠습니까?"
5. → 설치 및 포스팅

## Integration with AGENTS.md

이 스킬은 AGENTS.md의 지침을 따릅니다:

- 외부 작업(이메일 발송, 포스팅 등)은 반드시 확인
- 자동 설치는 안전한 스킬에 한함
- 주인님의 workspace에 설치된 스킬만 관리
