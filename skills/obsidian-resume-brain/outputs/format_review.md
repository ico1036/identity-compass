# Resume Format Review — Quant Industry Standards Audit
**Date:** 2026-03-23 | **Resumes Reviewed:** 10

---

## Per-Resume Issues

### 1. resume_jump_v3.md
- **Length:** ~45 lines of content. Fits 1 page ✅
- **Section order:** Summary → Experience → Education → Research Highlights → Skills. Has "Role-fit Addendum" at bottom — **remove this**; looks like cover letter bleed.
- **Bullets:** Mostly good action-verb format. The two standalone bullets at end of Level 3 (sensitivity analysis, kill rules) are orphaned — no sub-header.
- **Red flag:** "Research 90% / Trader 10%" label is unusual and could confuse recruiters.

### 2. resume_millennium_v3.md
- **Length:** ~45 lines. 1-page ✅
- **Same issues as Jump:** Role-fit Addendum present. Orphaned bullets under Level 3. "Research 90% / Trader 10%."
- Nearly identical to Jump — differentiation is minimal.

### 3. resume_bridgewater_v2.md
- **Length:** Significantly longer (~70+ lines of dense content). **Will exceed 1 page easily — likely 2 pages.** Acceptable for Bridgewater but borderline.
- **Format:** Uses tab-separated header instead of pipe-separated — **inconsistent** with all other resumes.
- **No ## SUMMARY header** — summary is an unlabeled paragraph.
- **Section order:** Experience → Skills → Education → Publications. **Skills before Education is non-standard.**
- **Bullets:** No bullet markers (–) used; plain text paragraphs in places. Inconsistent with other resumes.
- **Placeholder present:** `[backtest result: Sharpe X.XX, ann. return XX% — to be updated]` — **must fill or remove before submission.**
- **Positive:** Most detailed Skills section across all resumes. Publications section with DOI — good.
- **Red flag:** "Layer" terminology instead of "Level" — inconsistent with other resumes.

### 4. resume_gic_v3.md
- **Length:** ~45 lines. 1-page ✅
- **Section order:** Standard ✅
- **Good addition:** "Delivered dashboard tools for model governance" — unique to this version, strong for GIC.
- **Same orphaned bullets issue** under Level 3.
- **No Role-fit Addendum** — cleaner. ✅

### 5. resume_point72_v3.md
- **Length:** ~40 lines. Compact, 1-page ✅
- **Clean and focused.** Minimal issues.
- **Same orphaned bullets.** Same "Research 90% / Trader 10%."

### 6. resume_qcp_v3.md
- **Length:** ~45 lines. 1-page ✅
- **Summary mentions** "digital-asset relevant risk framing" — good targeting.
- **"Ph.D. Physics"** in summary vs "Ph.D. Particle Physics" everywhere else — **inconsistent.**
- **Same orphaned bullets issue** — actually fixed here, bullets integrated under Level 3 properly. ✅

### 7. resume_fionics_v3.md
- **Length:** ~55 lines. **Borderline 1-page** — summary is very long (5 lines).
- **Summary is too long.** "Goal: build Agentic Hedgefund capability inside the next firm—hiring one person but gaining scalable quant team architecture." — **Overly bold/presumptuous for a resume.** Reads like a pitch, not a summary.
- **Duplicate publication:** ACAT 2021 listed twice in Research Highlights (once as award, once as publication line).
- **Skills:** Includes Claude Agent SDK, Google ADK — good for this target.

### 8. resume_worldquant_v1.md
- **Length:** ~50 lines. 1-page ✅
- **Has a "Research Infrastructure" sub-section** outside the Level structure — structural deviation.
- **Level 1 is too thin** — only 2 bullets vs 3-4 in other resumes. Unbalanced.
- **Good:** Summary explicitly mentions WorldQuant by name — proper targeting.

### 9. resume_x4alpha_v1.md
- **Length:** ~50 lines. 1-page ✅
- **Has "Research Infrastructure — Built from Scratch"** section — good for startup context.
- **Skills formatted differently** — uses bold sub-categories (Core, ML/Data, AI Agents, Infra). **Inconsistent** with pipe-separated format in other resumes. Actually better format — consider standardizing all to this.
- **Summary:** "Looking for a high-autonomy seat where one researcher can have outsized impact" — strong startup framing ✅

### 10. resume_bonhill_crypto_hft_v1.md
- **Length:** ~50 lines. 1-page ✅
- **Has "Signal Research & Crypto-Relevant Capabilities"** section — good targeting.
- **Skills include "Interests" line** — unusual for quant resumes but acceptable for crypto/HFT.
- **SQL missing from Languages** (present in all other resumes) — **inconsistency.**
- **Research Highlights condensed** to 2 bullets — less detail than others.

---

## Cross-Resume Consistency Issues

| Issue | Affected Resumes |
|---|---|
| **Orphaned bullets** (sensitivity analysis + kill rules floating without sub-header) | Jump, Millennium, GIC, Point72 |
| **"Research 90% / Trader 10%"** label — non-standard, could confuse | Jump, Millennium, GIC, Point72, QCP, Fionics |
| **Skills format inconsistency** — pipe-separated (7 resumes) vs bold-categorized (3 resumes) | X4Alpha, Bonhill use categorized; Bridgewater uses detailed list |
| **"Level" vs "Layer"** terminology | Bridgewater uses "Layer"; all others use "Level" |
| **Ph.D. descriptor** — "Particle Physics" vs "Physics" | QCP says "Physics"; all others say "Particle Physics" |
| **Header format** — pipe-separated vs tab-separated | Bridgewater uses tabs; all others use pipes |
| **Role-fit Addendum** present | Jump, Millennium only |
| **Date format** — all use "2019 – 2024" style consistently ✅ | N/A |
| **SQL listed** in skills | Missing from Bonhill |

---

## Top 5 Formatting Fixes Needed

1. **Remove "Role-fit Addendum"** from Jump and Millennium. If you need role-fit framing, integrate it into the Summary. An "addendum" section looks like a template artifact.

2. **Fix orphaned bullets.** The sensitivity analysis and kill rules bullets floating at the end of Level 3 in 4 resumes need to be either (a) integrated into Level 3's bullet list, or (b) given a sub-header like "Risk Governance" or "Model Discipline."

3. **Standardize Skills format.** Pick one: either bold-categorized (X4Alpha style — recommended, more readable) or pipe-separated (current majority). Apply consistently across all 10.

4. **Trim Fionics summary.** Cut from 5 lines to 2-3. Remove the "Goal: build Agentic Hedgefund" sentence — too presumptuous. Let the experience section speak for itself.

5. **Fix Bridgewater formatting.** Convert tabs to pipes in header, add `## SUMMARY` header, move Skills after Education, remove placeholder `[Sharpe X.XX]`, and change "Layer" → "Level" for cross-resume consistency.

---

## Additional Recommendations

- **Remove "Research 90% / Trader 10%"** from all resumes. This is internal self-assessment, not a standard quant resume convention. Replace with natural language in the summary (e.g., "research-focused" or "systematic research with PM collaboration").
- **GPA:** Not listed anywhere. For a Korean PhD this is acceptable — GPA culture differs. However, if GPA is strong (≥3.8/4.0 or equivalent), add it.
- **Publications:** Only Bridgewater has a proper Publications section with DOI. Consider adding a single-line publication reference to all resumes (ACAT 2021 with DOI).
- **Certifications:** None listed (CFA, FRM, etc.). Not a red flag for PhD quant researchers, but worth noting.
- **Contact info:** Complete across all resumes ✅ (email, phone, LinkedIn).

---

## Overall Market-Readiness Score

| Dimension | Score | Notes |
|---|---|---|
| Content quality | 8/10 | Strong 3-level narrative, real metrics, live deployment |
| Formatting consistency | 5/10 | Too many cross-resume inconsistencies |
| Quant signal clarity | 7/10 | Value prop clear in ~30 sec; orphaned bullets hurt flow |
| Targeting/customization | 8/10 | Good per-firm tailoring in summaries |
| Red flags | 6/10 | Placeholder text, Role-fit Addendum, "Research 90%/Trader 10%" |
| **Overall** | **6.5/10** | Strong content held back by formatting inconsistencies |

**Bottom line:** The content is genuinely strong — real AUM, live deployment, quantified results, CERN pedigree. The main drag is presentation consistency. Fix the top 5 issues above and this becomes an 8/10 package.
