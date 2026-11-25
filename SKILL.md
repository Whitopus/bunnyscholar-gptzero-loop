---
name: bunnyscholar-gptzero-loop
version: 1.2.0
source: https://raw.githubusercontent.com/Whitopus/bunnyscholar-gptzero-loop/main/SKILL.md
repo: https://github.com/Whitopus/bunnyscholar-gptzero-loop
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

本技能协同复用以下现有能力：
1. **`bunnyscholar-api` 技能**：负责 BunnyScholar 开放平台核心接口协议、计费规则（20–500 计费字符）与错误码约定。
2. **`credentials` 技能**：负责安全凭据验证与无回显终端录入协议，严禁将任何真实 `sk-` API Key 暴露到上下文或聊天历史中。
3. **内置 `browser` Subagent**：负责打开 `https://bunnyscholar.cn/developer` 引导新用户注册领额/建 Key，以及驱动 `https://app.gptzero.me` 进行免费 Basic Scan（Model 5.0b）与 `Page by page scan` 分页自检。

## Quick Start

1. **前置确认与静默探针**（若未装 `bunnyscholar-api`，先按上方前置提示安装；在论文工作目录运行时请使用 Skill 目录下的脚本绝对路径，macOS/Linux 可使用 `python3`；即使无 Word/LibreOffice 仍可用纯文本框快测降 AI）：
   ```bash
   python scripts/humanizer_loop.py check-env --output env_status.json
   ```
   若 `found` 为 `false`，按 [onboarding_guide.md](./references/onboarding_guide.md) 引导用户无回显写入 `~/.env` 后再复跑。

2. **基线解析与快照备份**（对照 `summary.body_para_indices` 定位正文段号，勿盲猜 `1,2,3`）：
   ```bash
   python scripts/humanizer_loop.py inspect --docx paper.docx --output inspect.json
   python scripts/humanizer_loop.py snapshot --docx paper.docx --overall-human 0 --note "baseline" --output snap_v1.json
   ```

3. **拟人改写与无损回写（一字不改 + 整段或局部子串涂黄）**：
   ```bash
   python scripts/humanizer_loop.py humanize --input target_paras.json --output humanized.json
   python scripts/humanizer_loop.py apply --docx paper.docx --humanized humanized.json --highlight-paras 6,7,8 --output apply_res.json
   ```

4. **导出 PDF 并暂存至内置浏览器沙箱上传目录**：
   ```bash
   python scripts/humanizer_loop.py export-pdf --docx paper.docx --stage-to "<ArtifactDir>/browser_sandbox/uploads" --output pdf_res.json
   ```

## Utility Scripts

核心脚本 [humanizer_loop.py](./scripts/humanizer_loop.py) 全部采用 `argparse` 子命令模式，结构化结果统一写入 `--output <file.json>`：

| 子命令 | 核心作用 | 关键参数示例 |
| :--- | :--- | :--- |
| `check-env` | 静默探测 `BUNNYSCHOLAR_API_KEY`、PDF 后端、`bunnyscholar-api` 与远程版本（2s 超时/24h 缓存） | `[--skip-update-check \| --force-update-check] [--output env.json]` |
| `self-update` | 安全更新本技能（Git 目录走 `git pull --ff-only`，非 Git 目录按白名单下载） | `[--apply] [--output update.json]` |
| `inspect` | 解析 `.docx` 正文角色（`body_para_indices`）、硬分页（`page_break_paras`）、高亮、引文与第一人称（自动忽略 URL 与直接引语） | `--docx paper.docx [--output inspect.json]` |
| `snapshot` | 备份当前 `.docx` 至 `.snapshots/v{N}_{timestamp}.docx` 并记录实测得分 | `--docx paper.docx [--overall-human 96] [--pages "1=99,2=98"] [--note "..."]` |
| `rollback` | 查看历史得分对比表，或回滚至指定版本 / 历史最高分快照 | `--docx paper.docx (--list \| --version 2 \| --best)` |
| `humanize` | 限流调用 `/api/open/humanizer`，支持语言/平台/门禁灵活开关 | `--input in.json --output out.json [--dual-stage] [--language en] [--platform gptzero] [--allow-first-person] [--max-word-len 16] [--disable-quality-gate]` |
| `apply` | 将 API 原文**一字不改**写入指定段落，支持整段涂黄或 JSON 内 `highlight_substrings` 局部涂黄 | `--docx paper.docx --humanized out.json [--highlight-paras 6,7] [--clear-other-highlights]` |
| `export-pdf` | Windows 优先 Word COM 导出（保超链接与高亮），跨平台 fallback LibreOffice `soffice` | `--docx paper.docx [--pdf out.pdf] [--stage-to <uploads_dir>] [--backend auto\|word\|soffice]` |

`humanize` / `apply` 的 JSON 支持可选局部涂黄字段：
```json
{
  "paragraphs": [
    {
      "para_index": 6,
      "text": "Full paragraph text...",
      "highlight_substrings": ["revised phrase to highlight"]
    }
  ]
}
```

## Workflow

1. **前置、环境检查、更新提示与目标基准确认**：确保已按 `https://bunnyscholar.cn/skills/bunnyscholar-api.md` 安装 `bunnyscholar-api` 并完成 `check-env`；若 `update.update_available` 为 `true`，礼貌询问用户是否运行 `self-update --apply`（或 `git pull --ff-only`）升级后再继续（绝不静默自改代码）；缺失 Key 时按 [onboarding_guide.md](./references/onboarding_guide.md) 引导无回显写入 `~/.env`。**开工前轻问一轮用户的期望 AI 率基准**（例如总体/每页希望 AI 率低于多少%，如 `AI <= 15%` / `Human >= 85%` 或更严格的全绿 `>= 90%`，以及是否允许第一人称、是否需要局部涂黄；用户已明确或选择默认时直接按 `Human >= 85%` 推进）。
2. **基线快照与首轮测试**：对 `.docx` 执行 `inspect`（读取 `summary.body_para_indices` 区分页眉元信息与正文段号）与 `snapshot`；若用户尚未提供报告，使用 `export-pdf --stage-to` 并按 [gptzero_browser_sop.md](./references/gptzero_browser_sop.md) 获取 `Page by page scan` 基线。
3. **分页冻结与源稿预处理**：“先一后二”——先在源稿修正错词、人称、逻辑、生硬分号与 Peer Review 语法，顽固页剥离 AI 八股连接词（详见 [anti_ai_playbook.md](./references/anti_ai_playbook.md)）。**`Human >= 85%` 或纯白的页面/段落坚决冻结不动**。
4. **拟人改写、实时报费与语义体检**：仅对未达标段落调用 `humanize`（顽固页升档 `--dual-stage`）。**每轮调用结束后主动向用户汇报本轮实际扣费**（读取输出 JSON 中的 `total_usage_amount`，如 `¥0.229 CNY`）与门禁重刷次数。脚本自动执行质量门禁后，Agent 仍应快速通读返回文本检查是否存在语义反意（如把“焦虑”改反）；若有，只能改源稿重调或重刷，**绝不手改**。
5. **原样落盘与精准涂黄**：调用 `apply` 一字不改写入 `.docx`（整段修订用 `--highlight-paras`，局部微调在 JSON 中传 `highlight_substrings`）。
6. **复测、快照与不完美结果半途询问**：
   - 局部单段迭代优先复用同一 `browser` Subagent 会话，在 GPTZero 首页**纯文本框粘贴快测**（零上传确认弹窗、极省 credits）；仅在首轮基线与最终交付验收时 `export-pdf` 上传整篇 PDF 获取 `Page by page scan` 分页得分（遇 `Advanced` 假 429 试用弹窗，自动连环关掉切回 `Basic Scan` 即可）。
   - 随即执行 `snapshot` 记录新得分；若退步，立即 `rollback --best` 恢复历史最高分。
   - **半途询问机制（Checkpoint Confirmation）**：当某轮复测处于“明显好转但尚未达到约定基准”的不完美状态（例如 `Human 53% / AI 47%` 或个别页卡在 `Human 79%`）时，应如实汇报当前得分与本轮/累计花费，主动询问用户是**继续攻坚下一轮（深改源稿 / `--dual-stage`）**、**见好就收锁定当前版**，还是**回滚上一高分快照**（若用户事先开启 `/goal` 攻坚到底则直接冲向约定基准）。

## Final Delivery Report（最终交付战报清单）

闭环全部完成后，建议向用户呈现清晰透明的 5 维度战报（对照初始约定基准，灵活组织，不僵化）：
1. **最终版 AI 率全览**：整体结论与三维概率（`Human% / Mixed% / AI%` 对比基线与目标基准）、逐页 `Page by page scan` 得分表、各正文段标黄与作业高亮核验。
2. **顽固段落迭代复盘**：明确指出哪几段改了多轮、反复原因（如八股模板 / 语义反意 / 孤页）、最终破局方式与保留快照版本。
3. **GPTZero 额度耗费**：初始与最终剩余 credits、总扫描轮次（文本框快测 vs PDF 分页终检）、是否触发换号。
4. **BunnyScholar API 耗费**：每轮及累计调用次数、门禁重刷次数、累计真实扣费金额（元 CNY）。
5. **交付物路径、报告 PDF 与勿手改提醒**：最终 `.docx`/`.pdf` 路径、**最终版对应的 GPTZero 原生 PDF 检测报告**（在结果页点击 `Export` 导出并归档交付，受限时降级为分享链接 + 分页截图，按需附带）、最佳快照号与回滚命令，并提醒成品直接提交、严禁手改标点或润色。

## Rate Limiting

- **跨进程文件锁限流**：BunnyScholar 单 Key 官方限流约为 `1800 次 / 60 秒`（30 req/s）。`humanizer_loop.py` 默认收紧至 **≤ 20 req/s**，结合 `time.monotonic()` 与跨进程锁文件（Windows `msvcrt.locking` / POSIX `fcntl.flock`）确保多 Agent 并发安全。
- **退避重试与错误透明**：遇 HTTP `429`（支持解析 `Retry-After`）或 `5xx` 瞬时错误自动指数退避重试；遇 `400`/`401`/`402`/`403` 非重试错误直接透传响应体与充值/密钥链接并退出。
- **单次长度限制**：拟人改写接口要求单次文本在 **20–500 计费字符**（英文约 60–1500 字母），超长段落须在句号处拆分后再调用。

## Common Mistakes

1. **手改或让 AI 二次润色 API 返回文本**：哪怕只微调末尾 1 句话或几个标点，GPTZero 也会立刻将其标为 `Your most AI sentences` 第一名。所有内容修改必须在调用 `humanize` **之前**完成。
2. **被 `Mixed 99% / AI 1% / Human 0%` 假通关误导**：仅看 AI 概率低于 5% 不算真正通关，必须拿下 GPTZero 总体绿标 `Human` 且确保 `Page by page scan` 各页达标。
3. **盲猜 `para_index` 为 `1,2,3`**：真实论文前几段常是姓名、课程、日期、标题与 Thesis；务必先看 `inspect` 返回的 `summary.body_para_indices` 再决定操作段落。
4. **在 GPTZero 误点付费标签页或绕过人机校验**：日常轮测务必停留在免费的 **Basic Scan（Model 5.0b）** 与 `Page by page scan`；遇 hCaptcha/Turnstile 或登录拦截必须暂停交由用户在可见浏览器窗口手动完成。
5. **正文段间硬分页产生“2 行孤页”**：强制硬分页会导致末尾出现仅 2 行的孤页，触发 GPTZero `Too short to scan` 误判或拉低整页得分；应取消正文段间硬分页并开启孤行控制。
