---
name: juinnim-maps-search
description: Find places with Google Maps without Maps API. Use when user asks for nearby places (e.g., nearest mart/cafe/hospital), route links, or map search results. Build Google Maps search/directions links and provide concise Korean results.
---

# juinnim-maps-search

Use this skill when the user wants Google Maps-style place search but no Maps API is available.

## Core Policy

- Do not claim precise distance/time unless a reliable source is available.
- Prefer giving a working Google Maps link immediately.
- If exact "nearest" is requested, provide top candidates and ask user to confirm final pick if ambiguity remains.

## Fast Workflow

1. Normalize user location text (Korean/English mixed allowed).
2. Build a direct Google Maps search link first:
   - `https://www.google.com/maps/search/?api=1&query=<URL_ENCODED_QUERY>`
3. If user asks for "nearest", run web search with local Korean query and extract strong candidates.
4. Return:
   - best candidate(s)
   - map links
   - optional next action (navigation link)

## Link Templates

### Place search

```text
https://www.google.com/maps/search/?api=1&query=<query>
```

Example query: `광교센트럴타운62단지 근처 대형마트`

### Directions (origin -> destination)

```text
https://www.google.com/maps/dir/?api=1&origin=<origin>&destination=<destination>&travelmode=driving
```

Allowed `travelmode`: driving, walking, transit

## Response Style (Korean)

- Keep it short and practical.
- Always include at least one clickable Google Maps link.
- When confidence is low, state that clearly and offer to refine with one follow-up question.

## Typical Prompts

- "지금 내 위치 기준 가장 가까운 대형마트 찾아줘"
- "여기서 스타벅스 제일 가까운 곳"
- "출발지 A에서 B까지 지도 링크"

## Limits

- No direct geolocation access unless user provides location text/coordinates.
- No hidden Maps API calls.
- If user needs exact live nearest ranking, ask for current coordinates and provide map links for confirmation.
