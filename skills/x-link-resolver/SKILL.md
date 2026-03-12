---
name: x-link-resolver
description: Resolve and summarize X (Twitter) post URLs when direct fetch fails or returns login/error pages. Use when a user shares x.com / twitter.com status links and asks to read, extract, summarize, or fact-check the post content, especially when web_fetch is blocked.
---

# X Link Resolver

## Overview
Extract readable content from X post URLs with a fallback flow: try lightweight fetch first, then switch to full browser rendering if blocked.

## Workflow

1. Normalize URL.
   - Accept `x.com` or `twitter.com` status links.
   - Keep original URL for citation.

2. Try lightweight fetch first.
   - Use `web_fetch` on the post URL.
   - If content is usable, extract core text and stop.

3. Fallback to browser rendering when blocked.
   - Trigger fallback if `web_fetch` shows errors like login wall, “Something went wrong”, empty content, or obvious anti-bot page.
   - Use `browser.open` on the same URL.
   - Wait briefly, then use `browser.snapshot`.

4. Extract post body and metadata from snapshot.
   - Capture account handle, timestamp, engagement numbers if visible.
   - Prefer the main article body over side panels/replies.
   - If the post is an article/thread-style long post, collect heading + key bullet/paragraph blocks.

5. Return structured output.
   - Include:
     - `access_method`: `web_fetch` or `browser_fallback`
     - `url`
     - `author`
     - `posted_at`
     - `main_text`
     - `key_points` (3-5 bullets)
   - If partial only, explicitly label as partial.

## Reliability Rules
- Do not use policy-violating bypass methods.
- Do not fabricate hidden content.
- If browser fallback still fails, ask user for paste/screenshot and continue from provided material.

## Response Template
Use this concise format when delivering results:

- 접근 방식: `<web_fetch|browser_fallback>`
- 원문 링크: `<url>`
- 작성자/시각: `<author, time if available>`
- 핵심 요약:
  1. ...
  2. ...
  3. ...
- 상태: `<full|partial>`
