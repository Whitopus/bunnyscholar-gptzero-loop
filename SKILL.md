---
name: bunnyscholar-gptzero-loop
description: >-
  Use BunnyScholar's Humanizer API for Chinese or English text, optionally review GPTZero results, and apply selected revisions to Word. Use for 拟人改写、降 AI 率、GPTZero 报告复核 or reversible DOCX revisions.
metadata:
  version: "1.3.0"
  source: https://raw.githubusercontent.com/Whitopus/bunnyscholar-gptzero-loop/main/SKILL.md
  repo: https://github.com/Whitopus/bunnyscholar-gptzero-loop
---

# BunnyScholar × GPTZero

Follow the user's text, language, target platform, scope, and deliverable. Use the CLI when it simplifies the work. A browser, Word/PDF tools, and a separately installed API skill are optional capabilities.

## Choose the shortest path that fits

| Request | Start here |
| --- | --- |
| First-time setup | If a key may already exist, run `check-env --quick --summary` and reuse it when found. For a new account, open BunnyScholar's homepage for sign-in. After the user signs in, resume in the same browser, open API Keys, and fill a convenient name if the browser supports it. Give the user the exact `setup-key` command before they create the key and paste it in their terminal. See the [setup guide](references/onboarding_guide.md). |
| Check or update the Skill | Run `self-update` to check the installed version. If the user asks to update, run `self-update --apply`, verify the reported version, and read the updated Skill before continuing. See the [update instructions](README.md#update). |
| Rewrite pasted text or a short text file | Read the selected text and identify what needs preserving before the first rewrite. Use `humanize --text-file paragraph.txt --output result.json --allow-quality-warnings` for one paragraph, or `--input` with JSON for a batch (each completed paragraph is checkpointed; pass `--resume` to continue an interrupted batch without re-billing). Use `--dry-run` when useful for checking length or estimating usage. Return a candidate and call out meaning or terminology issues that need review. |
| Interpret a GPTZero report | Start with the supplied report, screenshot, or share link. If the user wants a fresh result, use the available browser or ask for a new report only when access is blocked. See [GPTZero browser notes](references/gptzero_browser_sop.md). |
| Revise an existing Word file | Use `inspect` to identify paragraph IDs and compare them with the report. Work on a copy via `apply --output-docx` or keep a snapshot when editing in place (`apply` refuses to overwrite paragraphs containing embedded images, drawings, or footnote/endnote references). Check the affected paragraphs and layout. Export and scan a PDF only when page-level results matter. See the [Word and iteration notes](references/anti_ai_playbook.md). |

## Decide what to preserve before rewriting

- Inspect the selected text or supplied report yourself. Identify wording that must stay verbatim, wording worth keeping initially but open to later changes, and facts whose wording can vary. Start with a short list.
- When the proposed choices matter and the user has left them open, agree on the required wording and the room for later changes in one short exchange before the first API rewrite. Continue local preparation in the meantime. If the user has settled or delegated those choices, proceed within that scope. If no wording needs special protection, proceed directly.
- Pass the currently protected wording via `--personal-terms`. When a comparable scan stalls or a candidate reads rigidly, use later authorized rounds to loosen optional wording in small steps. Allow equivalent phrases first and consider broader changes to sentence structure if warranted. Keep required wording, factual meaning, and citations. Review `missing_personal_terms` and compare each candidate with the source and the best acceptable version. Ask again only if a useful next step would change a requirement or exceed the authorized scope or budget. See the [iteration example](references/anti_ai_playbook.md#loosen-wording).

## Help the user sign in or switch accounts

- If the user asks to sign in or switch accounts, or the requested feature reaches a sign-in barrier, take the current browser as far as it can go. Reuse a suitable session and open the actual sign-in or account menu yourself when browser control is available. If user action is needed, hand off the ready tab and name the control or choice visible now, what signals completion, and what you will do next. With no browser access, provide the direct service link and the shortest manual step.
- When the user says they are done, check the signed-in page in the same session, including any new tab opened by the site, and resume the original task. If the sign-in flow is still waiting for a user action, explain the specific step visible on screen. Ask for a screenshot or an existing report only when it can help resolve a remaining blocker.
- For account switching, use the site's available account controls and keep the current work ready to resume. If a choice is missing, ask only what changes the next step, such as which service to switch or whether BunnyScholar API calls need the other account too. Verify the new session before scanning or changing settings. See the [BunnyScholar setup guide](references/onboarding_guide.md) and [GPTZero browser notes](references/gptzero_browser_sop.md).

## Using the services

- For API parameters, supported platforms, and current pricing, use BunnyScholar's [official API reference](https://bunnyscholar.cn/skills/bunnyscholar-api.md). An installed `bunnyscholar-api` skill can help locate the details. The CLI defaults to `en` and `gptzero`. With `--language zh_CN`, the default platform is `cnki`. Each humanizer call takes 20–500 billable characters. `--dry-run` estimates the length and reference cost. Ask about a missing choice only when it affects the operation. For similarity-only requests, use the separate official academic rewrite endpoint.
- Keep credentials in the user's terminal or environment, outside chat and logs. `setup-key` reuses a configured key automatically. If it needs a new key, the user's interactive terminal handles hidden input and verifies the saved file. Authentication and balance are determined by the service.
- A live rewrite sends the selected text to BunnyScholar and can incur charges. After first-time setup, point the user to [usage and balance](https://bunnyscholar.cn/developer) and let them know they can [top up](https://bunnyscholar.cn/developer/recharge) if needed. For a larger batch, a local length estimate can help the user decide. An online scan sends content to the detector. Use the services within the requested scope and respect any budget or round limit.
- Preserve the original API response as a candidate. Before detector scoring, review each paragraph's `fidelity_warnings` for changed numbers, quantities with units, negations, and qualifiers. For a candidate from another source, `review-text` runs the same local check. Check the actual claims and citations as well, since unchanged terms can still carry a changed meaning. Keep the previous acceptable text if a fact was lost or changed. Attribute detector scores to the exact version scanned. See the [candidate review example](references/anti_ai_playbook.md#review-candidate).

Report the requested deliverables with relevant changes, any scans actually run, and the usage reported by the service when available. If the user wants a GPTZero report file, collect the native PDF report for the exact version scanned when the account offers it. See the [report export steps](references/gptzero_browser_sop.md#export-report). If there is no new measurement, say so. A newer Skill version can be mentioned when relevant and handled separately from the task. See [CLI examples](README.md#cli-tools).
