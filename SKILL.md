---
name: bunnyscholar-gptzero-loop
description: >-
  Use BunnyScholar's Humanizer API for Chinese or English text, optionally review GPTZero results, and apply selected revisions to Word. Use for 拟人改写、降 AI 率、GPTZero 报告复核 or reversible DOCX revisions.
metadata:
  version: "1.2.0"
  source: https://raw.githubusercontent.com/Whitopus/bunnyscholar-gptzero-loop/main/SKILL.md
  repo: https://github.com/Whitopus/bunnyscholar-gptzero-loop
---

# BunnyScholar × GPTZero

Follow the user's text, language, target platform, scope, and deliverable. Use the CLI when it simplifies the work. A browser, Word/PDF tools, and a separately installed API skill are optional capabilities.

## Choose the shortest path that fits

| Request | Start here |
| --- | --- |
| First-time setup | If a key may already exist, run `check-env --quick --summary` and reuse it when found. For a new account, open BunnyScholar's homepage for sign-in. After the user signs in, resume in the same browser, open API Keys, and fill a convenient name if the browser supports it. Give the user the exact `setup-key` command before they create the key and paste it in their terminal. See the [setup guide](references/onboarding_guide.md). |
| Rewrite pasted text or a short text file | Use `humanize --text-file paragraph.txt --output result.json --allow-quality-warnings` for one paragraph, or `--input` with JSON for a batch. Use `--dry-run` when useful for checking length or estimating usage. Return a candidate and call out meaning or terminology issues that need review. |
| Interpret a GPTZero report | Start with the supplied report, screenshot, or share link. If the user wants a fresh result, use the available browser or ask for a new report only when access is blocked. See [GPTZero browser notes](references/gptzero_browser_sop.md). |
| Revise an existing Word file | Use `inspect` to identify paragraph IDs and compare them with the report. Work on a copy via `apply --output-docx` or keep a snapshot when editing in place. Check the affected paragraphs and layout. Export and scan a PDF only when page-level results matter. See the [Word and iteration notes](references/anti_ai_playbook.md). |

## Using the services

- For API parameters, supported platforms, and current pricing, use BunnyScholar's [official API reference](https://bunnyscholar.cn/skills/bunnyscholar-api.md). An installed `bunnyscholar-api` skill can help locate the details. This CLI can run with a key alone. Default CLI parameters are `en` and `gptzero`; pass the requested settings explicitly when they differ, such as `--language zh_CN --platform cnki`. Ask about a missing choice only when it affects the operation. For similarity-only requests, the official academic rewrite endpoint is the relevant service.
- Keep credentials in the user's terminal or environment, outside chat and logs. `setup-key` reuses a configured key automatically. If it needs a new key, the user's interactive terminal handles hidden input and verifies the saved file. Authentication and balance are determined by the service.
- A live rewrite sends the selected text to BunnyScholar and can incur charges. After first-time setup, point the user to [usage and balance](https://bunnyscholar.cn/developer) and let them know they can [top up](https://bunnyscholar.cn/developer/recharge) if needed. For a larger batch, a local length estimate can help the user decide. An online scan sends content to the detector. Use the services within the requested scope and respect any budget or round limit.
- Use the browser tools available in the current host. If the site requires a sign-in or a human verification, let the user complete that step in the same session. Existing reports or user-provided results also work.
- Preserve the original API response as a candidate and review it for meaning, references, and technical terms. If you or the user edits the candidate, attribute any detector score to the version actually scanned. Page selection, highlighting, quality checks, retry count, and the stopping point are task decisions.

Report the requested deliverables with relevant changes, any scans actually run, and the usage reported by the service when available. If there is no new measurement, say so. A newer Skill version can be mentioned when relevant and handled separately from the task. See [CLI examples](README.md#cli-tools).
