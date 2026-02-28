# US-Iran Crisis Dashboard (local)

빠르게 실행 가능한 로컬 대시보드입니다.

## Run

```bash
cd war-dashboard
python3 server.py
```

브라우저: http://127.0.0.1:8787

## What it does

- RSS 기반 다중 소스 수집 (Reuters/AP/BBC/Google News/Al Jazeera)
- 키워드 연관도 + 소스 신뢰도 가중 점수
- 2분마다 자동 갱신
- 티커형 헤드라인 표시

## Notes

- "모든 매체" 100% 커버는 API/접근제한으로 현실적으로 어려움
- X(Twitter) 실시간 고신뢰 수집은 공식 API 연동이 가장 안전
- 필요 시 Telegram 알림/cron 브리핑으로 연동 가능
