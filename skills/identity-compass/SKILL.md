---
name: identity-compass
description: >
  Hyper-personalized decision compass that extracts your values and choices as vectors from
  everyday conversations, computes your true life direction (H vector) and alignment score (M)
  using physics-inspired magnetization + Bayesian updates, and visualizes everything as an
  interactive decision map. No forms, no questionnaires — just talk. Use when facing career
  moves, life decisions, identity questions ("who am I?", "is this right for me?"), or
  comparing opportunities. Includes dialectical dialogue, decision simulation, and Obsidian
  vault integration for persistent memory.
---

# Identity Compass 🧭

대화에서 의사결정 벡터를 추출하고, 스핀/자기장 물리 모델 + 베이지안 업데이트로
**H 벡터(목표 방향)**와 **M(정렬도)**를 계산하는 초개인화 나침반.

## 핵심 개념

- **H 벡터** = 사용자의 궁극적 방향 (자기장). Phase 1 변증법으로 추출.
- **구슬(v_i)** = 개별 의사결정 스핀. 각각 방향·가중치·정렬도를 가짐.
- **M(자화도)** = 모든 구슬이 H와 얼마나 정렬되었는가. 0~1.

---

## Phase 1: H 벡터 추출 (변증법적 대화)

직접 "목표가 뭐예요?"라고 묻지 않는다. 모순, 감정 반응, 반복 주제에서 **역추론**한다.

### 대화 시작 안내 (첫 세션에서만)
"몇 가지 질문을 드릴 건데, 언제든 '그만', '다음으로', '충분해'라고 하시면
거기서 멈추고 바로 지금까지 파악된 내용으로 정렬도를 계산해드릴게요."

### 변증법 대화 유형 (순서대로)
1. **딜레마형** — 긴장을 만들어 가치관 드러냄
2. **시점 이동형** — 메타 관점 활성화 ("5년 전의 당신이 지금 당신을 본다면?")
3. **모순 짚기형** — 불일치 명시해 정교화 유도
4. **완료형** — "사실 이미 답을 알고 있지 않나요?"

7개 핵심 차원 상세 프로토콜: `references/dialectical-protocol.md`

### H 벡터 구성

```yaml
H:
  core_values: ["자율적 사고", "깊이 있는 연구"]     # 반복 등장 가치
  anti_values: ["단순 실행", "타인 시선 의존"]        # 거부 반응 보인 것
  direction: [0.85, 0.70, 0.90]                      # 3D 단위벡터
  domain_weights:                                      # 삶의 영역별 중요도
    career: 0.8
    family: 0.6
    health: 0.5
    finance: 0.4
    growth: 0.7
  confidence: 0.65                                     # 0~1, 대화 쌓일수록 상승
  one_liner: ""                                        # 본질 포착 한 줄 (아래 참조)
  last_updated: "2026-03-22"
```

confidence < 0.4이면 정렬도 계산 전에 대화를 더 진행한다.

### H 한 줄 요약 원칙
가치 나열이 아닌, **그 사람의 본질을 포착하는 문장 하나**.
- ❌ "가족 시간, 자율성, 안정을 중시함"
- ✅ "안정보다 자율을 택하되, 가족과 함께할 수 있는 삶의 속도를 지키는 사람"

### 3D 축 정의
- **X축**: 자율성(+) ↔ 구조(-) — autonomy vs structure
- **Y축**: 깊이(+) ↔ 폭(-) — depth vs breadth
- **Z축**: 혁신(+) ↔ 안정(-) — innovation vs stability

---

## Phase 2: 구슬 등록 & 베이지안 업데이트

### 벡터 수집 프로토콜

매 대화에서 의사결정/가치 판단 관찰 시 추출:

```yaml
what: "무엇을 선택/거부/선호했는가"
why_surface: "사용자가 말한 이유"
why_essence: "LLM이 판단한 근본 이유"
direction: [x, y, z]     # 3D 단위벡터
intensity: 0.0-1.0       # 반응 강도
confidence: 0.0-1.0      # 추출 확신도
weight: 1-10             # 구슬 가중치 (아래 기준표)
domain: "career"         # 삶의 영역
timestamp: "2026-03-22"
```

### 구슬 가중치(w) 자동 평가 기준표

| 기준 | 낮음 (1-3) | 중간 (4-6) | 높음 (7-10) |
|------|-----------|-----------|------------|
| 재무적 변화 | 커피값 | 월급 10% | 집/직장/투자 |
| 시간적 구속 | 하루 | 수개월 | 수년 이상 |
| 비가역성 | 쉽게 취소 | 번복 비용 있음 | 되돌리기 매우 어려움 |
| 감정 강도 | 무덤덤 | 불안/기대 | 강한 두려움/흥분 |
| 언급 빈도 | 처음 나옴 | 2-3회 언급 | 반복적으로 언급 |

### 구슬 감쇄 규칙
- 6개월 이상 + 가중치 3 이하 → "오래된 구슬" 태그, 영향력 절반
- 일반 시간 감쇄: `decay = 0.95^(days/30)` (월 5%)

### 베이지안 업데이트

```
posterior ∝ prior × likelihood
```

각 차원을 Beta(α, β) 분포로 모델링. 상세: `references/bayesian-update.md`

### 정렬도(M) 계산

```
alignment_i = cos(v_i, H) - overlap(v_i, anti_values)
M = Σ(w_i × alignment_i) / Σ(w_i)
```

M 해석:
- **+0.7 ~ +1.0**: 강하게 정렬 — "나침반이 목표를 가리키고 있어요"
- **+0.3 ~ +0.7**: 대체로 맞음 — "약간의 조정이 있으면 더 선명해질 것 같아요"
- **-0.3 ~ +0.3**: 혼돈 — "여러 방향을 동시에 잡으려 하고 있어요"
- **-0.7 ~ -0.3**: 역행 — "현재 패턴이 목표와 반대 방향이에요"
- **-1.0 ~ -0.7**: 강하게 역행 — "중요한 무언가를 재검토할 시점이에요"

---

## Phase 3: 새로운 의사결정 지원

사용자가 새 선택을 고민할 때:
1. 선택지 A, B를 각각 가상 구슬로 변환
2. ΔM_A = M(현재 + A), ΔM_B = M(현재 + B) 계산
3. 결과 전달:

"[선택지 A]를 가상으로 추가했을 때, 전체 정렬도가 [현재 M] → [M+A]로 변합니다.
[선택지 B]는 [M+B]가 됩니다. [A/B]가 [구체적 가치들]과 더 잘 맞습니다.
다만 [주의할 점]은 지켜봐야 할 것 같아요."

---

## 백그라운드 신호 감지 레이어

모든 대화에서 상시 작동. 사용자는 인식하지 못한다.

### Step 1: 신호 감지

| 신호 유형 | 예시 발화 | 해석 |
|----------|----------|------|
| 부러움 | "그 사람처럼 살고 싶다" | 언급된 삶의 방식 → H 후보 |
| 피로/거부 | "이건 정말 못 하겠어" | 해당 가치 → anti_values 강화 |
| 몰입 | "시간 가는 줄 몰랐어" | 해당 활동 → core_values 강화 |
| 반복 언급 | 같은 주제 3회 이상 | 가중치 높은 구슬 후보 |
| 감정 극단 | 강한 불안·흥분·후회 | 해당 구슬 가중치 상향 |
| 모순 발화 | 이전 발언과 충돌 | H confidence 하향, 재탐색 필요 |

### Step 2: 신호 타입 분류 (Classification-First)

감지된 신호를 **먼저 3가지 타입으로 분류**한 뒤, 타입별 추출 전략을 적용한다.
동일한 벡터 포맷으로 무조건 변환하지 않는다 — 타입이 추출 방식을 결정한다.

| 타입 | 해당 신호 | 추출 전략 | weight 보정 |
|------|----------|----------|------------|
| `decision` | 선택, 거부, 지원, 수락/거절 | direction + intensity 중심. 구슬 가중치 기준표 그대로 적용 | 기본값 |
| `emotion` | 부러움, 피로, 몰입, 감정 극단 | core_values / anti_values 강화 중심. 방향보다 **어떤 가치가 자극됐는지**에 집중 | intensity × 1.2 |
| `pattern` | 반복 언급, 모순 발화 | H confidence 조정 중심. 벡터 생성보다 **기존 H/벡터의 신뢰도 재평가**가 목적 | frequency 기반 (3회=×1.0, 5회=×1.5, 7회+=×2.0) |

**타입별 상세:**

**decision (의사결정형)**
가장 직접적인 벡터 소스. 선택/거부 행위 자체가 방향을 나타낸다.
- 추출: 표준 벡터 포맷 (what, why, direction, weight 전부)
- 예: "A사 오퍼 거절했어" → direction 추출, weight 기준표 적용

**emotion (감정형)**
행동이 아닌 감정 반응. 방향보다 가치 체계의 강화/약화 신호.
- 추출: direction은 관련 가치 축 기준으로 단순화, intensity를 1.2배 증폭
- 예: "그 사람 보면 부럽다" → 부러운 대상의 삶의 방식을 direction으로, intensity × 1.2
- core/anti_values 업데이트가 주 목적이므로, 독립 구슬보다 기존 H 보정에 활용

**pattern (패턴형)**
단일 발화가 아닌 누적 패턴. 벡터를 새로 만들기보다 기존 데이터의 신뢰도를 조정.
- 반복 언급: 해당 주제 관련 기존 벡터의 weight 상향 (frequency 기반)
- 모순 발화: H confidence 하향 + 충돌 지점 기록 → /lint에서 모순 벡터로 감지
- 독립 구슬 생성하지 않음 — 기존 벡터/H의 메타데이터 업데이트

### Step 3: raw_signals.md 기록

저장: `obsidian-vault/compass/signals/raw_signals.md`에 조용히 누적.
각 신호에 타입 태그를 함께 기록:

```markdown
- [2026-04-06] [emotion] "그 사람 보면 솔직히 부럽다" → 자율적 라이프스타일 방향
- [2026-04-06] [decision] A사 최종 면접 거절 → 구조적 환경 거부 신호
- [2026-04-06] [pattern] "자율성" 5회째 언급 → autonomy-first 클러스터 weight 상향
```

신호 5개 이상 누적 시 /update를 자연스럽게 제안:
"최근 대화에서 몇 가지 패턴이 보이던데, 한번 나침반 업데이트해볼까요?"

---

## 커맨드

### /compass — 전체 시각화

`scripts/visualize_spins.html`을 렌더링. 사양:
- 흰 배경 + 초록 H 필드라인 (자기장 방향)
- H 고정 화살표 (사용자 조절 불가)
- 각 구슬: 크기=가중치(w), 색=정렬도(보라/주황/회색), 화살표=v_i 방향, 점선 호=H와의 각도 차
- 호버 시 스프링 애니메이션 + 툴팁 (정렬도·가중치·방향각)
- 구슬 클릭 → 해당 구슬 분석 대화 트리거
- 하단: H 배지 + 한 줄 요약 + 신뢰도 + 마지막 업데이트
- 우하단: M 수치 오버레이

### /update — H 업데이트 & 구슬 재평가

세션 대화형. 순서:
1. **무의식 신호 요약**: 최근 raw_signals를 보여줌
   "최근 대화에서 이런 신호들을 감지했어요:
   - '그 사람 보면 솔직히 부럽다' → 창의적 자율성 방향 신호
   - '요즘 너무 피곤해' → 과도한 야근 반가치 강화 신호"
2. **H 업데이트 확인**: 승인 → H 재계산, 수정 요청 → 변증법 추가 탐색
3. **구슬 재평가**: 오래된 구슬 재검토 제안
   "'야근 수락' 구슬이 등록된 지 3개월이 됐어요. 지금도 같은 방향인가요?"
4. **/compass 자동 실행**으로 마무리

### /lint — 나침반 건강검진

벡터·클러스터·H/M 상태를 자동 점검하고 이상 항목을 리포트.
주기적으로 제안하거나, 사용자가 직접 호출.

**5가지 체크 항목:**

1. **모순 벡터 감지**
   같은 도메인에서 cosine(v_i, v_j) < -0.3인 벡터 쌍 탐색.
   → "career 도메인에서 '자율성 추구'와 '안정적 대기업 선호'가 충돌합니다. 어느 쪽이 지금의 당신에 더 맞나요?"

2. **고아 벡터 감지**
   `cluster` 필드가 비어있거나, 해당 클러스터 노트가 존재하지 않는 벡터.
   → "3개 벡터가 클러스터에 연결되지 않았습니다. 기존 클러스터에 배정하거나 새 클러스터를 만들까요?"

3. **H-M 괴리 체크**
   H confidence > 0.7인데 M < 0.3 (방향은 확실한데 행동이 안 따라감),
   또는 H confidence < 0.4인데 M > 0.7 (방향이 불확실한데 행동은 일관됨).
   → "방향에 대한 확신은 높은데, 최근 선택들이 그 방향과 맞지 않고 있어요. 무슨 일이 있었나요?"

4. **오래된 벡터 감지**
   6개월 이상 경과 & 미재평가 벡터 목록.
   → "다음 5개 구슬이 6개월 이상 됐습니다. 지금도 유효한지 확인해볼까요?"

5. **미처리 신호 체크**
   `raw_signals.md`에 벡터로 변환되지 않은 신호가 5개 이상.
   → "처리되지 않은 신호가 7개 있어요. /update로 정리해볼까요?"

**출력 형식:**

```
🔍 나침반 건강검진 결과

✅ 모순 벡터: 없음
⚠️ 고아 벡터: 2건
   - "프리랜서 탐색" (2026-02-15) — 클러스터 미연결
   - "팀 리드 경험" (2026-01-20) — 클러스터 [[leadership]] 노트 없음
✅ H-M 괴리: 정상 (H conf 0.72, M 0.68)
⚠️ 오래된 벡터: 3건 (6개월+, 미재평가)
✅ 미처리 신호: 2건 (임계치 미만)

권장 조치: 고아 벡터 클러스터 배정 → /update 실행
```

**log.md 기록**: lint 실행 결과를 `type: lint`로 자동 append.

---

## 출력 모드

### 1. 나침반 모드 🧭
축적된 벡터의 궁극적 방향 + H 한 줄 요약 + M 수치

### 2. 이력서 모드 📄
벡터 기반 강점/서사 생성 → `obsidian-resume-brain` 연동
클러스터에서 핵심 강점 3-5개 추출, 구체적 사례와 함께 서사화

### 3. 회사 매칭 모드 🏢
회사 JD/문화를 벡터화 → 사용자 벡터와 코사인 유사도 계산
→ `company-fit-research` 연동

### 4. 의사결정 보정 모드 ⚖️
현재 선택 방향과 H의 각도 계산 + Phase 3 가상 구슬 시뮬레이션

### 5. 자화도 리포트 📊
전체 정렬도 + 클러스터별 분석 + 시각화

---

## Obsidian Vault 구조

```
obsidian-vault/compass/
  prior/              ← Phase 1 토론 결과
  vectors/            ← 개별 구슬(벡터) 노트
  clusters/           ← 상위 방향성 클러스터
  signals/            ← 백그라운드 감지 신호
    raw_signals.md    ← 누적 신호 로그
  magnetization.md    ← H + M + posterior
  timeline.md         ← 방향성 변화 히스토리
  log.md              ← append-only 작업 이력 (아래 참조)
  _MOC.md             ← compass 전체 조망
```

### log.md 포맷 (append-only 작업 이력)

모든 H/M/벡터 변경을 시간순으로 기록. 에이전트가 직접 append한다.
`timeline.md`가 방향성 변화의 해석을 담는다면, `log.md`는 **사실 기록**.

```markdown
## [2026-03-22] ingest | execution-heavy 거부
- type: vector_add
- vector: direction [0.8, -0.6, 0.3], weight 7, domain career
- M: 0.68 → 0.72 (+0.04)

## [2026-03-25] update | H 재계산
- type: h_update
- H confidence: 0.65 → 0.72
- H direction: [0.80, 0.70, 0.90] → [0.83, 0.72, 0.88]
- trigger: 신호 5개 누적

## [2026-04-01] lint | 건강검진
- type: lint
- 모순 벡터: 1건 (career 도메인)
- 고아 벡터: 2건
- 오래된 벡터: 3건
- action: 사용자에게 재평가 제안

## [2026-04-02] decision_sim | A사 vs B사
- type: decision_sim
- option_a: A사 → M 0.72 → 0.76 (+0.04)
- option_b: B사 → M 0.72 → 0.65 (-0.07)
```

**type 값**: `vector_add`, `vector_update`, `vector_archive`, `h_update`, `m_recalc`, `lint`, `decision_sim`, `signal_batch`

**규칙**:
- 항상 최신 항목이 맨 아래 (append-only)
- 파이프라인 실행할 때마다 자동 기록
- 삭제하지 않는다 — 이력은 영구 보존

---

### 벡터 노트 형식

```yaml
---
type: vector
date: 2026-03-19
what: "execution-heavy 거부"
why_surface: "단순 실행 역할은 재미없다"
why_essence: "자율적 사고 > 지시 수행"
direction: [0.8, -0.6, 0.3]
intensity: 0.9
confidence: 0.85
weight: 7
domain: career
cluster: "[[autonomy-first]]"
tags: [career, preference, anti]
---
```

---

## 스크립트

| 스크립트 | 용도 |
|---------|------|
| `scripts/export_vectors.py` | vault 벡터 노트 → vectors.json |
| `scripts/calculate_magnetization.py` | 자화도 계산 → magnetization.json + .md |
| `scripts/visualize_2d.html` | 2D 인터랙티브 시각화 (다크 테크 테마) |

---

## 자동화 파이프라인 (필수)

**에이전트는 벡터를 추출할 때마다 아래 전체 파이프라인을 실행해야 한다.**
수동 개입 없이, 대화 속에서 자동으로 완료되어야 함.

### 트리거 조건
- 새 의사결정/선호/거부/가치 시그널 감지 시
- /update 커맨드 실행 시
- /lint 커맨드 실행 시 (log.md 기록만)
- Phase 1 완료 시

### 파이프라인 단계

```
1. 시그널 감지 → 신호 타입 분류 → 타입별 벡터 추출
2. Obsidian vault에 벡터 노트 생성/업데이트
3. vectors.json 업데이트 (전체 벡터 목록)
4. magnetization.json 재계산 (H, M, clusters)
5. compass_data.json 자동 생성 ← ⚠️ 이 단계를 빠뜨리지 말 것!
6. log.md에 작업 이력 append ← ⚠️ 이 단계도 빠뜨리지 말 것!
```

### Step 5: compass_data.json 자동 생성

vectors.json + magnetization.json → compass_data.json 변환.
시각화(`visualize_2d.html`)가 이 파일을 로드하므로 반드시 갱신.

**생성 규칙:**

```python
# vectors.json의 각 벡터를 identity/opportunities로 분류
identity_beads = []   # domain이 career/growth/life이고 기회(회사)가 아닌 것
opportunity_beads = [] # 회사/포지션 관련 벡터

for v in vectors:
    bead = {
        "what": v["what"],
        "why": v["why_essence"],
        "dir": v["direction"],
        "w": v["weight"],
        "cl": classify_color(v),  # 아래 기준 참조
        "status": v.get("status", "")
    }
    if is_opportunity(v):
        bead["match"] = cosine_similarity(v["direction"], H["dir"])
        opportunity_beads.append(bead)
    else:
        identity_beads.append(bead)

compass_data = {
    "identity": identity_beads,
    "opportunities": opportunity_beads,
    "H": {"dir": magnetization["magnetization_vector"], "mag": magnetization["magnetization_magnitude"]},
    "oneLiner": magnetization.get("H_one_liner", ""),
    "clusters": [
        {"name": name.upper(), "m": c["magnetization"], "color": cluster_colors[name]}
        for name, c in magnetization["clusters"].items()
    ]
}
```

**색상 분류 기준 (cl 필드):**

| cl 값 | 조건 |
|--------|------|
| `identity` | 개인 정체성/가치 벡터 (회사가 아님) |
| `hot` | 기회 + cosine match ≥ 0.85 |
| `active` | 기회 + 이미 지원/제출 완료 |
| `warm` | 기회 + match 0.65~0.85 |
| `tension` | 기회 + H와 방향 충돌 있음 (match < 0.6이면서 weight ≥ 6) |
| `cool` | 기회 + match 0.5~0.65 |
| `avoid` | 기회 + match < 0.5 또는 anti-value 충돌 |

**클러스터 색상 기본값:**

```json
{
  "autonomy-first": "#00c8ff",
  "depth-builder": "#a855f7",
  "innovation-drive": "#00ff88"
}
```

### 저장 위치

모든 JSON 파일은 `scripts/` 디렉토리에 저장:
```
scripts/
├── vectors.json          # 전체 벡터 목록
├── magnetization.json    # H + M + clusters
├── compass_data.json     # 시각화용 (자동 생성)
├── sample_data.json      # 데모용 (수정 금지)
└── visualize_2d.html     # 시각화 UI
```

> ⚠️ **에이전트 필수 행동**: 벡터를 추가/수정할 때마다 Step 3→4→5를 반드시 순차 실행.
> compass_data.json이 없거나 오래되면 시각화가 빈 화면 또는 구버전을 보여준다.

---

---

## 주의사항

- H는 **절대 확정적으로 선언하지 않는다**. "지금까지 대화에서 느낀 건..." 식으로 잠정 표현.
- M 수치는 정밀 계산이 아닌 추정임을 숨기지 않는다.
- **결정을 내려주지 않는다.** 정렬도 정보를 주고 판단은 사용자에게 돌린다.
- 변증법 대화를 불편해하면 즉시 전환한다.
- H가 시간이 지나며 바뀔 수 있음을 자연스럽게 다룬다.
  "예전과 원하는 게 달라진 것 같아요" 신호 감지 → H 업데이트 제안.
