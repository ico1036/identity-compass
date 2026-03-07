---
name: juinnim-schedule
description: Manage Jiwoong Kim's personal calendar quickly via gws CLI. Use when user asks about upcoming schedule (especially next 1-7 days), asks to add/edit/delete events, asks for daily briefing, or asks for availability checks.
---

# juinnim-schedule

Use `gws` CLI for all calendar actions.

## Core Rules

- Treat timezone as `Asia/Seoul` unless the user specifies otherwise.
- 핵심 원칙: 사용자가 일정 관련 질문을 하면, 기본 추측하지 말고 `gws` CLI로 해당 기간을 조회해 답한다.
- 기간이 명시되지 않으면 한 줄로 되묻는다. (예: "오늘/이번주/다음주 중 어느 범위로 볼까요?")
- Prefer `calendarId: "primary"`.
- Always summarize results in concise Korean.
- After create/update/delete, confirm completion with event title and time.

## Quick Commands

### 1) Schedule check (기간 지정 조회)

```bash
gws calendar events list --params '{
  "calendarId":"primary",
  "timeMin":"<YYYY-MM-DD>T00:00:00+09:00",
  "timeMax":"<YYYY-MM-DD>T00:00:00+09:00",
  "singleEvents":true,
  "orderBy":"startTime",
  "maxResults":50
}'
```

### 2) Add event

```bash
gws calendar events insert --params '{"calendarId":"primary"}' --json '{
  "summary":"<제목>",
  "start":{"dateTime":"<YYYY-MM-DD>T<HH:MM>:00+09:00","timeZone":"Asia/Seoul"},
  "end":{"dateTime":"<YYYY-MM-DD>T<HH:MM>:00+09:00","timeZone":"Asia/Seoul"}
}'
```

### 3) Update event time/title

```bash
gws calendar events patch --params '{"calendarId":"primary","eventId":"<EVENT_ID>"}' --json '{
  "summary":"<새 제목>",
  "start":{"dateTime":"<새 시작>","timeZone":"Asia/Seoul"},
  "end":{"dateTime":"<새 종료>","timeZone":"Asia/Seoul"}
}'
```

### 4) Delete event

```bash
gws calendar events delete --params '{"calendarId":"primary","eventId":"<EVENT_ID>"}'
```

## Response Format (default)

- 일정 조회:
  - 기간
  - 총 일정 개수
  - 각 일정의 날짜/시간/제목
- 일정 추가/수정/삭제:
  - 작업 성공 여부
  - 제목
  - 시간

## Error Handling

- `403 access_denied`: OAuth test user or consent issue. Guide user to OAuth consent screen/test users.
- `401 No credentials provided`: run `gws auth login` first.
- Missing/ambiguous time: ask one concise clarification question before writing.
