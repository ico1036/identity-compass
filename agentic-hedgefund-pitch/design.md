# Agentic Hedgefund Pitch Deck Design Guide

## 1) Design System (Institutional / Credible / Premium)

### 1.1 Color System
- **Primary Navy**: `#0E1A2B` (신뢰, 기관 톤, 배경/헤더)
- **Deep Slate**: `#1F2A3A` (본문 타이틀, 보조 배경)
- **Signal Blue**: `#2F6BFF` (핵심 강조, 링크, 액션 포인트)
- **Risk Amber**: `#D89B2B` (주의/리스크 관련 하이라이트)
- **Safe Green**: `#1F9D6E` (통제/검증 통과 상태)
- **Neutral Gray 1**: `#F4F6FA` (섹션 배경)
- **Neutral Gray 2**: `#D9DFEA` (구분선/그리드)
- **Text Main**: `#0F1724`, **Text Sub**: `#5B677A`

**Usage Rule**
- 한 슬라이드 내 강조색은 최대 1개(필요 시 2개)만 사용
- Risk 주제는 Amber, Governance 통과는 Green으로 일관 매핑
- 브랜드 신뢰감 유지를 위해 고채도 색 남용 금지

### 1.2 Typography
- **Korean/English Primary Font**: Pretendard / Inter (fallback: Noto Sans KR)
- **Title**: 34-40pt, SemiBold
- **Section Header**: 24-28pt, SemiBold
- **Body**: 16-18pt, Regular
- **Footnote / Source**: 11-12pt, Regular

**Type Rule**
- 한 슬라이드 텍스트 라인 수 최대 28줄
- 문장형보다 명사형/동사형 bullet 우선
- 영어 용어는 짧게 괄호 처리 (예: Out-of-Sample, OOS)

### 1.3 Spacing & Layout
- **Grid**: 12-column grid, 좌우 margin 64px
- **Base Spacing Unit**: 8px
- **Section Gap**: 32-40px
- **Card Padding**: 20-24px

**Layout Rule**
- 60/40 또는 50/50 분할 레이아웃 우선
- 도표/다이어그램은 슬라이드 면적 최소 35% 확보
- 정보 위계: Title → Key Message → Evidence Bullets → Note

---

## 2) Chart Styles

### 2.1 Core Chart Types
- **Comparison**: Bar (Traditional vs Agentic)
- **Process**: Loop/Flow Diagram (Research→Dev→Backtest→Self-feedback)
- **Governance**: Layered Shield / Funnel
- **Timeline**: Stage-Gate Roadmap
- **Economics**: Dual-axis (Unit Cost down, Throughput up)

### 2.2 Chart Styling Rules
- 축, 레이블, 범례는 최소 요소만 남기기 (noise 제거)
- 숫자보다 **의사결정 의미(So What)**를 캡션으로 명시
- baseline/assumption 존재 시 하단에 간결 표기
- 3D 차트, 과도한 그라데이션, 복잡한 패턴 금지

---

## 3) Iconography
- **Style**: 단색(Line + Fill minimal) 아이콘, 라운드 코너 2px
- **Stroke**: 1.5~2px 통일
- **Size**: 20/24/32px 세 가지 스케일만 사용
- **Semantic Mapping**
  - Engine/Automation: 기어 + 회로
  - Governance/Risk: 방패 + 체크/알림
  - Scale/Economics: 공장 + 상승/하강 화살표
  - Team Architecture: 사람 1 + 다중 노드

**Rule**: 장식용 아이콘 금지. 아이콘은 의미 전달 보조 역할만.

---

## 4) Data Callout Rules
- 핵심 데이터는 슬라이드당 **최대 3개 callout**
- 형식: **숫자/지표 + 한 줄 의미 + 판단 연결 문장**
  - 예: “Cycle Time -35% → 검증 속도 개선 → 파일럿 의사결정 리드타임 단축”
- 불확실성 데이터는 confidence band/범위로 표기
- 추정치(estimate)는 반드시 “Assumption” 태그 부착
- 과거 성과 제시 시 기간/조건/OOS 여부 동시 표기

---

## 5) Do / Don’t Examples

### Do
- 메시지를 “투자자 질문” 기준으로 배열 (왜, 어떻게, 얼마나, 리스크는)
- Slide 6(거버넌스)에 가장 높은 시각적 신뢰도 부여
- CTA는 명령형이 아니라 합의형 문장으로 제시
- 각 슬라이드마다 1개의 핵심 take-away만 남기기

### Don’t
- 기술 스택 상세 설명(모델명/파라미터/코드 수준) 과다 노출
- 성과 암시 그래프를 근거 없이 과장 표현
- 한 슬라이드에 다이어그램 + 표 + 장문 텍스트 동시 배치
- 색상으로만 의미 구분(아이콘/라벨 병행 필수)

---

## 6) Per-slide Design Intent Map (10 Slides)

1. **Slide 1 (Executive Thesis)**
   - Intent: 첫 인상에서 프리미엄 기관 톤 확립
   - Visual Priority: 중앙 허브형 메시지 구조
   - Emphasis Color: Signal Blue 1포인트

2. **Slide 2 (Allocator Problem)**
   - Intent: Pain 공감 및 변화 필요성 부각
   - Visual Priority: 비교 테이블 + 1개 핵심 콜아웃
   - Emphasis Color: Neutral 중심, 문제 항목만 Amber

3. **Slide 3 (AI-native Engine)**
   - Intent: 철학의 본체를 구조적으로 이해시키기
   - Visual Priority: 입력-처리-출력 엔진 도식
   - Emphasis Color: Blue/Slate 조합

4. **Slide 4 (Automation Loop)**
   - Intent: 반복 가능성과 학습 속도 전달
   - Visual Priority: 원형 루프 + 단계 시간 라벨
   - Emphasis Color: Blue 흐름선

5. **Slide 5 (Alpha Factory Economics)**
   - Intent: 확장성/비용 효율의 비즈니스 설득
   - Visual Priority: Unit Cost vs Throughput 이중 그래프
   - Emphasis Color: Green(개선), Gray(기준선)

6. **Slide 6 (Risk Governance)**
   - Intent: 신뢰 확보의 핵심 슬라이드
   - Visual Priority: 3-layer 방패형 통제 체계
   - Emphasis Color: Amber(위험), Green(통제)

7. **Slide 7 (Team Architecture)**
   - Intent: 인력 리스크를 시스템 우위로 전환
   - Visual Priority: 1 Human + Multi-agent 조직도
   - Emphasis Color: Blue 노드 연결

8. **Slide 8 (Allocator Fit)**
   - Intent: 실제 배분 기준과의 정합성 입증
   - Visual Priority: 요구사항 매트릭스 + 체크맵
   - Emphasis Color: Green 체크 포인트

9. **Slide 9 (Deployment Model)**
   - Intent: 도입 장벽 최소화 및 실행 경로 명확화
   - Visual Priority: 3단계 Stage-Gate 타임라인
   - Emphasis Color: 단계 게이트에 Blue 포인트

10. **Slide 10 (Close & Ask)**
   - Intent: 행동 유도(Deep-dive/Pilot 합의)
   - Visual Priority: Decision Ladder + Next Actions 박스
   - Emphasis Color: Signal Blue + 최소 Green

---

## 7) Philosophy-to-Visual Mapping (필수 반영 체크)
- **AI-native quant research engine** → Slide 3 엔진 구조의 메인 비주얼
- **End-to-end automation loop** → Slide 4 원형 루프의 핵심 내러티브
- **Alpha factory (cost-efficient scaling)** → Slide 5 이코노믹스 차트
- **Uncertainty/risk governance (Stress, OOS, Kill rules)** → Slide 6 통제 프레임
- **Hire 1 = scalable team architecture** → Slide 7 조직도 메시지

---

## 8) v200 Execution Plan (Design Track)
- **Phase A (v1-v40)**: 템플릿/그리드/타이포 고정, 색상 일관성 확보
- **Phase B (v41-v100)**: 차트/도식 정교화, 슬라이드별 시선 흐름 최적화
- **Phase C (v101-v160)**: 투자자 피드백 반영, 복잡도 20% 축소
- **Phase D (v161-v200)**: 최종 QA (가독성, 신뢰감, 일관성) + 배포본 확정
