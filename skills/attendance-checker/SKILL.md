---
name: attendance-checker
description: Parse meeting/Zoom chat logs to extract attendance, cross-check against a roster, and update a Google Sheets attendance spreadsheet. Use when the user pastes chat text and asks to check attendance, create or update an attendance sheet, or generate attendance statistics. Supports Korean chat formats (N조_이름), 출석 keyword detection, and monthly recurring attendance tracking.
---

# attendance-checker

Parse meeting chat logs → extract attendees → update Google Sheets.

## Workflow

1. **Receive chat text** from user (Zoom chat export, copy-paste)
2. **Parse** with `scripts/parse_attendance.py` to extract names, groups, check-ins
3. **Cross-check**: compare 출석 writers vs chat participants, flag discrepancies
4. **Present stats** to user for confirmation
5. **Update sheet** with `scripts/update_sheet.py` via gws CLI

## Parsing Chat

Save chat text to a temp file, then:

```bash
python3 scripts/parse_attendance.py -f /tmp/chat.txt
# With roster cross-check:
python3 scripts/parse_attendance.py -f /tmp/chat.txt -r /tmp/roster.json
```

**Roster JSON format:**
```json
[{"group": 1, "name": "홍길동"}, {"group": 2, "name": "김철수"}]
```

Output: JSON with attendees, check-in status, message counts, group stats, anomalies.

## Updating Google Sheets

**New sheet:**
```bash
python3 scripts/update_sheet.py --sheet-id SHEET_ID --date 2026-03-21 \
  --attendance attendance.json --roster roster.json --new
```

**Add column to existing sheet:**
```bash
python3 scripts/update_sheet.py --sheet-id SHEET_ID --date 2026-04-18 \
  --attendance attendance.json
```

New attendees not in the roster are auto-appended with 신청여부=X.

## Chat Format

Expects Zoom-style chat: `HH:MM:SS From N조_이름 : message`

- Group format: `N조_이름` or `N조 이름` (underscore or space)
- Check-in keyword: `출석` or `츌석` (common typo)
- Reactions/replies are counted as participation but not as 출석

## Stats to Present

Before updating the sheet, always show:
- Total participants vs explicit check-ins
- People who chatted but didn't write 출석 (⚠️)
- People with no group assignment (미배정)
- Group-by-group breakdown
- If roster provided: registered-but-absent list

## Sheet Structure

| 조 | 이름 | 신청여부 | 2026-03-21 | 2026-04-18 | ... |
|----|------|---------|------------|------------|-----|

- 신청여부: O=registered, X=walk-in
- Each date column: O=attended, X=absent
- New dates are appended as columns

## Current Sheet

- **Spreadsheet ID:** `1W6bW_elf5welrNQ4xre9ZFNb1zaW9CPfPCE641s7e0M`
- **Sheet name:** AI정기세션 출석부
- **URL:** https://docs.google.com/spreadsheets/d/1W6bW_elf5welrNQ4xre9ZFNb1zaW9CPfPCE641s7e0M/edit
