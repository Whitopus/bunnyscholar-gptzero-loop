---
name: bunnyscholar-gptzero-loop
description: >-
  Bunny学术（BunnyScholar）拟人改写 API 与 GPTZero 内置浏览器自检降 AI 率闭环工作流。
  支持零第三方依赖 Python 标准库 CLI、OpenXML 无损读写与指定段落黄色荧光笔高亮、
  跨进程限流与质量门禁自动重刷、快照备份与最佳版本回滚，以及双后端 PDF 导出。
  当用户需要降低英文学术论文的 GPTZero AI 率、保留 Word 原排版与超链接、
  或执行可回滚的分页降 AI 迭代时使用本技能。
---

# Bunny学术 × GPTZero 拟人化降 AI 闭环工作流（BunnyScholar-GPTZero Loop）

## Overview

本技能将学术写作降 AI 率从“盲目试错”固化为**可审计、可回滚、零幻觉篡改**的工程闭环（曾实战将 4 页论文从 100% AI 逆转至 4/4 页全部 `Human 99% / 98% / 97% / 87%`）：
- **大脑（AI Agent）**：解析 GPTZero 分页扫描结果、执行分页冻结（Freeze）、在送入 API 前先剥离 AI 八股套话与调整逻辑、驱动内置 `browser` Subagent 完成网页实测。
- **手脚（零依赖 CLI `scripts/humanizer_loop.py`）**：100% 基于 Python 3 标准库实现（兼容 `python`、`python3` 与 `uv run`，无需 `python-docx` 或 `pymupdf`），负责静默凭据探针、OpenXML 无损文本替换与黄色荧光笔高亮、跨进程限流与质量门禁重刷、快照备份回滚及双后端 PDF 导出。

## Dependencies

本技能**不重复造轮子**，明确协同复用以下现有能力：
1. **`bunnyscholar-api` 技能**：负责 BunnyScholar 开放平台核心接口协议、计费规则（20–500 计费字符）与错误码约定。
2. **`credentials` 技能**：负责安全凭据验证与无回显终端录入协议，严禁将任何真实 `sk-` API Key 暴露到上下文或聊天历史中。
3. **内置 `browser` Subagent**：负责打开 `https://bunnyscholar.cn/developer` 引导新用户注册领额/建 Key，以及驱动 `https://app.gptzero.me` 进行免费 Basic Scan（Model 5.0b）与 `Page by page scan` 分页自检。

## Quick Start

1. **静默检测环境与凭据**（绝不读取或打印 Key 明文）：
   ```bash
   python scripts/humanizer_loop.py check-env --output env_status.json
   ```
   若 `found` 为 `false`，按 [onboarding_guide.md](./references/onboarding_guide.md) 引导用户无回显写入 `~/.env` 后再复跑。

2. **基线解析与快照备份**：
   ```bash
   python scripts/humanizer_loop.py inspect --docx paper.docx --output inspect.json
   python scripts/humanizer_loop.py snapshot --docx paper.docx --overall-human 0 --note "baseline" --output snap_v1.json
   ```

3. **拟人改写与无损回写（一字不改 + 精准涂黄）**：
   ```bash
   python scripts/humanizer_loop.py humanize --input target_paras.json --output humanized.json
   python scripts/humanizer_loop.py apply --docx paper.docx --humanized humanized.json --highlight-paras 1,2,3 --output apply_res.json
   ```

4. **导出 PDF 并暂存至内置浏览器沙箱上传目录**：
   ```bash
   python scripts/humanizer_loop.py export-pdf --docx paper.docx --stage-to "<ArtifactDir>/browser_sandbox/uploads" --output pdf_res.json
   ```

## Utility Scripts

核心脚本 [humanizer_loop.py](./scripts/humanizer_loop.py) 全部采用 `argparse` 子命令模式，结构化结果统一写入 `--output <file.json>`（避免 stdout 倾倒海量 JSON）：

| 子命令 | 核心作用 | 关键参数示例 |
| :--- | :--- | :--- |
| `check-env` | 静默探测 `BUNNYSCHOLAR_API_KEY`、PDF 后端与 `bunnyscholar-api` 技能 | `[--env-paths ...] [--ignore-process-env] [--output env.json]` |
| `inspect` | 解析 `.docx` 正文编号、词数、现存高亮、引文 `[1]..[N]` 单调性与第一人称 | `--docx paper.docx [--output inspect.json]` |
| `snapshot` | 备份当前 `.docx` 至 `.snapshots/v{N}_{timestamp}.docx` 并记录实测得分 | `--docx paper.docx [--overall-human 96] [--pages "1=99,2=98"] [--note "..."]` |
| `rollback` | 查看历史得分对比表，或回滚至指定版本 / 历史最高分快照 | `--docx paper.docx (--list \| --version 2 \| --best)` |
| `humanize` | 限流调用 `/api/open/humanizer`，内置 3 项质量门禁自动重刷 | `--input in.json --output out.json [--dual-stage] [--rate-limit 20] [--max-retries 3]` |
| `apply` | 将 API 原文**一字不改**写入指定段落，无损保留排版与 `<w:hyperlink>` | `--docx paper.docx --humanized out.json [--highlight-paras 1,2,3] [--clear-other-highlights]` |
| `export-pdf` | Windows 优先 Word COM 导出（保超链接与高亮），跨平台 fallback LibreOffice `soffice` | `--docx paper.docx [--pdf out.pdf] [--stage-to <uploads_dir>] [--backend auto\|word\|soffice]` |

`humanize` 的 `--input` JSON 格式如下（`para_index` 为 1-based 正文段号，文本需在 20–500 计费字符内）：
```json
{
  "paragraphs": [
    { "para_index": 1, "text": "Paragraph text to humanize..." }
  ]
}
```

## Workflow

1. **环境检查与冷启动**：执行 `check-env`。若缺少 `BUNNYSCHOLAR_API_KEY`，严格按 [onboarding_guide.md](./references/onboarding_guide.md) 打开控制台并引导用户通过无回显终端命令写入 `~/.env`。
2. **基线快照与首轮测试**：对原稿执行 `inspect` 与 `snapshot`，并用 `export-pdf --stage-to` 导出基线 PDF；按 [gptzero_browser_sop.md](./references/gptzero_browser_sop.md) 驱动内置 `browser` Subagent 登录 GPTZero 获取基线 `Page by page scan` 分页得分。
3. **分页冻结与源稿预处理**：“先一后二”——先在源稿中修正错词、人称、逻辑及 Peer Review 语法问题，并在顽固页剥离 AI 八股连接词，详见 [anti_ai_playbook.md](./references/anti_ai_playbook.md)。**`Human >= 85%` 或纯白的页面/段落坚决冻结不动**。
4. **拟人改写与自动门禁**：仅对未达标段落调用 `humanize`（单阶段失败时升档 `--dual-stage` 开启 `needPlagiarismReduction=True`）。脚本自动拦截第一人称、>16 字母乱码拼接词或丢失引文 `[n]` 并重刷。
5. **原样落盘与涂黄**：调用 `apply` 将 API 返回文本**一字不改**写入 `.docx`（按需加 `--highlight-paras`）。
6. **复测、快照与最优回滚**：再次 `export-pdf` 并复用同一 `browser` Subagent 会话复测 GPTZero，随即执行 `snapshot` 记录新得分。若某轮出现倒退，立即用 `rollback --best` 恢复历史最高分版本。

## Rate Limiting

- **跨进程文件锁限流**：BunnyScholar 单 Key 官方限流约为 `1800 次 / 60 秒`（30 req/s）。`humanizer_loop.py` 默认收紧至 **≤ 20 req/s**，结合 `time.monotonic()` 与跨进程锁文件（Windows `msvcrt.locking` / POSIX `fcntl.flock`）确保多 Agent 并发安全。
- **退避重试与错误透明**：遇 HTTP `429`（支持解析 `Retry-After`）或 `5xx` 瞬时错误自动指数退避重试；遇 `400`/`401`/`402`/`403` 非重试错误直接透传响应体与充值/密钥链接并退出，绝不静默吞错。
- **单次长度限制**：拟人改写接口要求单次文本在 **20–500 计费字符**（英文约 60–1500 字母），超长段落须在句号处拆分后再调用。

## Common Mistakes

1. **手改或让 AI 二次润色 API 返回文本**：哪怕只微调末尾 1 句话或几个标点，GPTZero 也会立刻将其标为 `Your most AI sentences` 第一名。所有内容修改必须在调用 `humanize` **之前**完成。
2. **遗漏 `language="en"` 或 `platform="gptzero"`**：`humanize` 子命令已内置锁定这两个参数；若绕过脚本手动调 API 却漏传 `en`，将按中文知网规则处理导致效果失效。
3. **在 GPTZero 误点付费标签页或绕过人机校验**：日常轮测务必停留在免费的 **Basic Scan（Model 5.0b）** 与 `Page by page scan`；遇 hCaptcha/Turnstile 或登录拦截必须暂停交由用户在可见浏览器窗口手动完成，严禁尝试绕过。
4. **正文段间硬分页产生“2 行孤页”**：强制硬分页会导致末尾出现仅 2 行的孤页，触发 GPTZero `Too short to scan` 误判或拉低整页得分；应取消正文段间硬分页并开启孤行控制。
5. **改前忘记 `snapshot`**：降 AI 具备概率波动，未留快照一旦改差将无法无损回退至上一轮高分版本。
