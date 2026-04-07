# Cross-Resume Consistency Audit

**Date:** 2026-03-23
**Auditor:** Subagent (cross-audit)
**Ground Truth:** master_resume_base.md + Identity Compass

---

## Per-Resume Findings

### 1. resume_jump_v3.md

**CRITICAL:**
- ❌ Return: says "+39% cumulative return and +9% alpha" → must be "+43.54% cumulative return vs +35.90% benchmark (+7.64%p alpha)"
- ❌ Role: "Supported live strategy research" → should be "Led model development and live strategy research"
- ❌ Company: "Alpha Bridge (Asset Plus AM)" → "Alpha Bridge (formerly Asset Plus AM)"
- ❌ Best Paper: no venues specified → add "Korean Physical Society (2020), Korean Society for Computational Science and Engineering (2021)"

**MINOR:**
- Fund size mentioned as "$22M" only; consider adding "KRW 3.4B" for consistency

**Compass:** Tone is solid — research-focused, no fluff. "Supported" undersells autonomy.

---

### 2. resume_millennium_v3.md

**CRITICAL:**
- ❌ Return: "+39% cumulative return and +9% alpha" → "+43.54% cumulative return vs +35.90% benchmark (+7.64%p alpha)"
- ❌ Role: "Supported portfolio research, analytics, and monitoring" → "Led model development, portfolio research, and monitoring"
- ❌ Company: "Alpha Bridge (Asset Plus AM)" → "Alpha Bridge (formerly Asset Plus AM)"
- ❌ Best Paper: no venues → add venues

**MINOR:**
- Same $22M-only issue

**Compass:** Good depth. "Supported" misaligns with autonomy-first cluster.

---

### 3. resume_bridgewater_v2.md

**CRITICAL:**
- ❌ Company: "Alpha Bridge — Asset Plus AM" → "Alpha Bridge (formerly Asset Plus AM)"
- ❌ No return numbers stated (neither correct nor incorrect, but inconsistent with all other resumes)
- ❌ Best Paper: not mentioned at all — should add awards with venues
- ❌ Period says "Jan 2024 – Present" → should be "Jan 2024 – Dec 2024"

**MINOR:**
- Format differs significantly (no markdown headers, tab-separated contact). Consider standardizing.
- "1024-node" in publication vs "1,000+" elsewhere — minor but inconsistent

**Compass:** This resume has the most authentic depth-builder tone. Layered architecture framing is strong. No fluff.

---

### 4. resume_gic_v3.md

**CRITICAL:**
- ❌ Return: "+39% cumulative return and +9% alpha" → "+43.54% cumulative return vs +35.90% benchmark (+7.64%p alpha)"
- ❌ Role: "Supported research and monitoring" → "Led model development and research"
- ❌ Company: "Alpha Bridge (Asset Plus AM)" → "Alpha Bridge (formerly Asset Plus AM)"
- ❌ Best Paper: no venues → add venues

**MINOR:**
- "Led distributed deep learning workloads" — this is fine for CERN context but inconsistent with other resumes that don't say "Led" for CERN

**Compass:** Good. Dashboard/governance emphasis fits GIC's institutional culture without being fluffy.

---

### 5. resume_point72_v3.md

**CRITICAL:**
- ❌ Return: "+39% cumulative return and +9% alpha vs benchmark" → "+43.54% cumulative return vs +35.90% benchmark (+7.64%p alpha)"
- ❌ Role: "Contributed to live strategy research" → "Led model development and live strategy research"
- ❌ Company: "Alpha Bridge (Asset Plus AM)" → "Alpha Bridge (formerly Asset Plus AM)"
- ❌ Best Paper: no venues → add venues

**MINOR:** None

**Compass:** Clean. "Contributed" is the worst offender — directly contradicts autonomy-first identity.

---

### 6. resume_qcp_v3.md

**CRITICAL:**
- ❌ Return: "+39% cumulative return and +9% alpha" → "+43.54% cumulative return vs +35.90% benchmark (+7.64%p alpha)"
- ❌ Role: "Supported live model research" → "Led model development and live strategy research"
- ❌ Company: "Alpha Bridge (Asset Plus AM)" → "Alpha Bridge (formerly Asset Plus AM)"
- ❌ Best Paper: no venues → add venues

**MINOR:** None

**Compass:** Solid. Digital-asset framing is appropriate without overstretching.

---

### 7. resume_fionics_v3.md

**CRITICAL:**
- ❌ Return in summary: "+39% cumulative return, +9% alpha" → "+43.54% cumulative return vs +35.90% benchmark (+7.64%p alpha)"
- ❌ Company: "Alpha Bridge (Asset Plus AM)" → "Alpha Bridge (formerly Asset Plus AM)"
- ❌ Best Paper venue: "Korean Computational Engineering Society" → "Korean Society for Computational Science and Engineering"
- ❌ Role in bullets: "Supported research, portfolio construction" contradicts "Led model development" in summary → make bullets consistent with "Led"

**MINOR:**
- Summary has the return numbers but bullets don't repeat them — fine, but ensure summary numbers are correct

**Compass:** Summary is the most forward/ambitious. Agentic Hedgefund pitch is prominent. Authentic to innovation-drive cluster (0.91).

---

### 8. resume_worldquant_v1.md ✅

**CRITICAL:** None — this resume is the gold standard

**MINOR:**
- "Korean Society for Computational Science and Engineering" ✓ — correct

**Compass:** Excellent. Clean separation of simulation vs live. Factually precise. Depth-first.

---

### 9. resume_x4alpha_v1.md ✅

**CRITICAL:** None

**MINOR:**
- Return rounded to "+43.5% vs +35.9% (+7.6%p)" — acceptable rounding but differs from exact "+43.54% vs +35.90% (+7.64%p)" in worldquant. Consider standardizing.

**Compass:** Most autonomy-forward ("sole quant researcher", "high-autonomy seat"). Authentic.

---

### 10. resume_bonhill_crypto_hft_v1.md

**CRITICAL:**
- ❌ Role: "Supported model research and live monitoring" → "Led model development and live monitoring"

**MINOR:**
- CERN analogy to alpha signal extraction is a nice touch, fits the target

**Compass:** Good. Research-first framing for crypto is well-calibrated.

---

## MASTER FIX LIST

### Fix 1: Return Numbers (6 files)

**Files:** jump_v3, millennium_v3, gic_v3, point72_v3, qcp_v3, fionics_v3

Each file has slightly different phrasing. Exact replacements:

**resume_jump_v3.md:**
- Old: `contributing to +39% cumulative return and +9% alpha vs S&P 500 over 16 months`
- New: `delivering +43.54% cumulative return vs +35.90% benchmark (+7.64%p alpha) over 16 months`

**resume_millennium_v3.md:**
- Old: `contributing to +39% cumulative return and +9% alpha vs S&P 500 over 16 months`
- New: `delivering +43.54% cumulative return vs +35.90% benchmark (+7.64%p alpha) over 16 months`

**resume_gic_v3.md:**
- Old: `contributing to +39% cumulative return and +9% alpha vs S&P 500 over 16 months`
- New: `delivering +43.54% cumulative return vs +35.90% benchmark (+7.64%p alpha) over 16 months`

**resume_point72_v3.md:**
- Old: `supporting +39% cumulative return and +9% alpha vs benchmark over 16 months`
- New: `delivering +43.54% cumulative return vs +35.90% benchmark (+7.64%p alpha) over 16 months`

**resume_qcp_v3.md:**
- Old: `contributing to +39% cumulative return and +9% alpha vs S&P 500 over 16 months`
- New: `delivering +43.54% cumulative return vs +35.90% benchmark (+7.64%p alpha) over 16 months`

**resume_fionics_v3.md (summary):**
- Old: `+39% cumulative return, +9% alpha vs. S&P 500 over 16 months`
- New: `+43.54% cumulative return vs +35.90% benchmark (+7.64%p alpha) over 16 months`

### Fix 2: Company Name (6 files)

**Files:** jump_v3, millennium_v3, gic_v3, point72_v3, qcp_v3, fionics_v3

- Old: `Alpha Bridge (Asset Plus AM)`
- New: `Alpha Bridge (formerly Asset Plus AM)`

**resume_bridgewater_v2.md:**
- Old: `Alpha Bridge — Asset Plus AM`
- New: `Alpha Bridge (formerly Asset Plus AM)`

### Fix 3: Role Verb — "Led" not "Supported/Contributed" (7 files)

**resume_jump_v3.md:**
- Old: `Supported live strategy research and analytics for a US equity growth mutual fund`
- New: `Led model development and live strategy research for a US equity growth mutual fund`

**resume_millennium_v3.md:**
- Old: `Supported portfolio research, analytics, and monitoring for a US Equity Growth mutual fund`
- New: `Led model development, portfolio research, and monitoring for a US Equity Growth mutual fund`

**resume_gic_v3.md:**
- Old: `Supported research and monitoring for an AI-driven US Equity Growth mutual fund`
- New: `Led model development and research for an AI-driven US Equity Growth mutual fund`

**resume_point72_v3.md:**
- Old: `Contributed to live strategy research and monitoring for a US equity growth mutual fund`
- New: `Led model development and live strategy research for a US equity growth mutual fund`

**resume_qcp_v3.md:**
- Old: `Supported live model research and monitoring for a US equity growth mutual fund`
- New: `Led model development and live strategy research for a US equity growth mutual fund`

**resume_fionics_v3.md:**
- Old: `Supported research, portfolio construction, and performance monitoring for an AI-driven US Equity Growth mutual fund`
- New: `Led model development, portfolio construction, and performance monitoring for an AI-driven US Equity Growth mutual fund`

**resume_bonhill_crypto_hft_v1.md:**
- Old: `Supported model research and live monitoring for a US equity growth mutual fund`
- New: `Led model development and live monitoring for a US equity growth mutual fund`

### Fix 4: Best Paper Venues (6 files)

**Files:** jump_v3, millennium_v3, gic_v3, point72_v3, qcp_v3

- Old: `Best Paper Awards (2020, 2021); ACAT 2021 publication.`
- New: `Best Paper Award, Korean Physical Society (2020); Best Paper Award, Korean Society for Computational Science and Engineering (2021); ACAT 2021 publication.`

**resume_fionics_v3.md:**
- Old: `Korean Computational Engineering Society (2021)`
- New: `Korean Society for Computational Science and Engineering (2021)`

### Fix 5: Bridgewater Date Fix

**resume_bridgewater_v2.md:**
- Old: `Jan 2024 – Present`
- New: `Jan 2024 – Dec 2024`

### Fix 6: Bridgewater — Add Best Paper

Add to bridgewater_v2.md after the publication entry (or create a RESEARCH HIGHLIGHTS section):
- `Best Paper Award, Korean Physical Society (2020); Best Paper Award, Korean Society for Computational Science and Engineering (2021).`

---

## Cross-Resume Consistency Summary

| Check | jump | mill | bridge | gic | p72 | qcp | fion | wq | x4a | bon |
|-------|------|------|--------|-----|-----|-----|------|----|-----|-----|
| Return numbers | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Company name | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Role verb (Led) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ⚠️ | ✅ | ✅ | ❌ |
| Sharpe scoped | ✅ | ✅ | N/A | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PM sim-scoped | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Best Paper venues | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| Education dates | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| CERN 1000+ nodes | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Legend:** ✅ correct | ❌ needs fix | ⚠️ partial/different format

## Compass Alignment Notes

All resumes authentically reflect the depth-builder, autonomy-first, innovation-driven character. No corporate fluff detected. The main compass violation is the "Supported/Contributed" verb in 7 resumes — this directly undermines the autonomy-first cluster (0.75) and contradicts the ground truth that Ryan **led** model development. The honesty principle is well-maintained: Sharpe and PM ownership are correctly scoped to simulation/backtest contexts across all resumes.

**worldquant_v1** and **x4alpha_v1** are the cleanest — use as templates for future resumes.
