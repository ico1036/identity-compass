# MEMORY.md

## User profile (durable)
- User: Jiwoong Kim (Asia/Seoul).
- Goal: Build a Singapore quant job + resume system.
- Preferred process: **MD-first optimization, then DOCX**.
- Resume integrity rule: avoid overclaim; do not imply direct PM ownership unless explicitly true.
- Clarification: User explicitly stated they are PM for the Agentic Hedgefund context.
- Role target: Research 90%, Trader 10%.
- Avoid focus: execution-heavy, pure arbitrage, low-latency trading.

## Operating preference (critical)
- Before aggressive resume drafting, run an **identity-mapping phase** using Obsidian graph accumulation.
- Continuously extract from conversations (not only direct forms): strengths, identity, tone, decision criteria, preferences/anti-preferences.
- Continue collection until information gain plateaus, then start resume generation.
- Give frequent progress updates during long tasks.

## Identity Compass (2026-03-19~)
- 주인님 아이디어: 스핀/자기장 물리 모델로 의사결정 방향성 추적
- 개별 의사결정 = 스핀 벡터, AI가 추출 → 자화 방향(궁극적 지향) 계산
- 베이지안: Phase 1 변증법 토론 → prior, Phase 2 대화 데이터 → posterior update
- 3축: X=자율↔구조, Y=깊이↔폭, Z=혁신↔안정
- 스킬 위치: skills/identity-compass/
- Obsidian vault: obsidian-vault/compass/
- Three.js 3D 시각화 포함
- Phase 1 (prior 형성) 아직 미실행

## Identity Compass 시각화 (2026-03-22)
- 2D 구슬 차트 (3D 삭제)
- 로컬서버: localhost:8742/visualize_2d.html
- 축: "나만의 길을 만든다"↔"정해진 길을 따른다" / "새로운 걸 만든다"↔"검증된 걸 지킨다"
- life-compass 스킬과 병합 완료 (가중치 기준표, 감쇄규칙, 백그라운드 감지, /update 프로토콜)
- M = 0.675, H: "구조보다 자율을 택하되, 깊이 있는 연구로 혁신을 만드는 사람"

## 출석부 스킬 (2026-03-22)
- attendance-checker 스킬 생성
- AI정기세션 출석부 시트: 1W6bW_elf5welrNQ4xre9ZFNb1zaW9CPfPCE641s7e0M
- 월별 반복 작업

## 주인님 벡터 (추정, Compass Phase 1 전)
- 자율성: +0.85 (매우 강함) — PM, 아키텍트, 자기 방향 설정
- 깊이: +0.7 — first-principles, 본질 추구
- 혁신: +0.9 — Layer 1→2→3, Agentic, 스핀 모델 아이디어
- 리더: +0.75 — PM, 팀 리더, 설계자
- 핵심 가치: 정직성 > 임팩트 부풀리기, 본질 > 형식

## Helix 사업화 (2026-03-30~31)
- 에셋플러스 협조 거부 확인 (2026-03-31)
- 독자 노선 전환: 하이브리드 추천 (SG 프롭 + 알파 라이센싱)
- Apex EAM/Bell Rock/CV5 견적 이메일 초안 작성 완료
- VC 보고서 V2 (Ralph 86/100): helix_vc_report_v2.md
- 100x 검증 보고서: helix_verification_report.md
- 비용: Apex 연 $85K-$160K, 손익분기 AUM $5M
- MAS 처벌 실제 사례 확인 (Adrian Lee 4년 PO, Sun Weiyeh 징역 6개월)
- SG IT법인+배당: 불법이나 소수 고래면 적발 확률 낮은 회색지대

## 하나금융융합기술원 (2026-03-25~04-01)
- 서류 통과 → PT면접 확정
- 자소서 3편 완료 (지원동기/자기소개/역량기술)
- 희망연봉: 1억 제출
- PT 4장: 자기소개→대학원→L1,L2→L3 Alpha Factory+Helix
- 작업 디렉토리: hana-ti-pt/ (base.md, slide.md)

## Avellaneda-Stoikov 논문 스터디 (2026-03-28)
- 마켓메이킹 바이블, reservation price까지 완전 이해
- 스프레드 유도(δ*=(1/γ)ln(1+γ/k)) 진행 중

## Asset Attention Autoresearch (2026-04-04~)
- GitHub: ico1036/asset_attention — Karpathy autoresearch 기반 ETF 자산배분
- **미션 리셋 (2026-04-04)**: Attention 기반 implicit regime learning이 비타협적 목표
- 107 실험의 교훈: Sharpe greedy + "Complexity Must Be Earned" → attention 포기 탈선
- **Sharpe 버그 수정**: sqrt(252)→sqrt(50.4), 이전 값 2.24배 과대
- **Karpathy 리팩토링**: prepare.py에 모든 평가함수 격리 (에이전트 수정 불가)
- **2-Agent 구조**: Explorer(실험) + Critic(CIO 페르소나 검증, 매 5 exp)
- **v3 파일럿**: 4자산(SPY,TLT,GLD,SHY), 일간 리밸, sliding window 4636샘플, expanding window 17년 OOS
- MicroPatchAttention 268 params → 첫 결과 attention uniform (레짐 학습 제로)
- Portfolio Transformer 논문 참조: sliding window + expanding window가 학계 표준
- cron 자동 리스폰: 매 45분
- **핵심 원칙**: 주인님 대화 스타일(상식 검증, 데이터 여정, 논문 교차검증)을 Socratic Self-Check + Critic으로 내재화

## 이력서 현황 (2026-03-22)
- Bridgewater QD: V2 작성중
- 하나금융TI QR: 최종본 제출 완료
- MS Capital QR: 완료 (Ralph 73.6점), GDrive 업로드
- Team Lead Global Futures: 완료 (fit 62점)
- Paradex Lead Quant: 완료 (fit 75점)
- Lingjun PM/QR: 완료 (fit 75점)
- Millennium QR Equity: 완료 (fit 65점)
- Citadel Securities QR: 완료 (fit 65점)
- 회사명 표기: "Alpha Bridge (formerly Asset Plus AM)" (EN) / "에셋플러스자산운용 (現 Alpha Bridge)" (KR)
- 모든 DOCX에 placeholder 남아있음 (연락처, BS학교, Sharpe 등)
- 수상: 한국계산과학공학회 우수논문(2021), 한국물리학회 우수논문(2020)

## KRA 실전 교훈 (2026-03-29)
- 서울 7R+8R 전멸, 총 -44,800원
- 시도: V2모델, 풀괴리, 멀티에이전트토론, 조교사필터 → 전부 실패
- 핵심: (1) 단일레이스 ML로 시장 못 이김 (2) 시장 인기마가 대체로 맞음 (3) 조교사 승률 단독 팩터 금지 (킹마스터 조교사 4.7%→1착) (4) 백테스트 ROI 과적합 주의
- Autoresearch 48전략 중 유일한 +ROI: LGB hybrid+Kelly +8% (장기 521베팅)
- 결론: 경마 베팅은 장기 대량에서만 edge 가능, 단일레이스=도박
