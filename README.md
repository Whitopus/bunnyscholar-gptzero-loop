<a id="top"></a>
<div align="center">

[简体中文](#简体中文) · [English](#english)

# BunnyScholar × GPTZero Loop

面向 AI Agent 的 Bunny学术（BunnyScholar）× GPTZero 降 AI 率助手：段落改写、报告复核导出、无损写回 Word

[![MIT License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](#install)
[![Agent Skill](https://img.shields.io/badge/Agent-Skill-orange)](SKILL.md)
[![Visitors](https://visitor-badge.laobi.icu/badge?page_id=Whitopus.bunnyscholar-gptzero-loop)](https://github.com/Whitopus/bunnyscholar-gptzero-loop)

[⚡ 一句话安装](#install) · [🔑 配置 Key](#setup-key) · [💬 怎么开口用](#first-prompt) · [🧰 命令行速查](#cli-tools) · [🔧 排错与文档](#troubleshooting)

</div>

---

<a id="简体中文"></a>

## 简体中文

<a id="quick-start"></a>
<a id="install"></a>

### ⚡ 一句话安装（推荐）

> [!IMPORTANT]
> **最省事的安装方式是把这句话发给支持本地 Skills 的 Agent。**

```text
请安装 https://github.com/Whitopus/bunnyscholar-gptzero-loop 到当前客户端的 Skills 目录，然后运行快速自检。优先复用我已有的 Key。如果缺 Key，请先打开 BunnyScholar 官网引导我登录，再告诉我去哪创建 Key，并给我一条带完整脚本路径的配置命令。
```

<details>
<summary>我想手动安装（Git 克隆 / 下载 ZIP）</summary>

选择当前客户端对应的一行，在 PowerShell、Bash 或 Zsh 中执行：

```sh
# Codex（当前用户）
git clone https://github.com/Whitopus/bunnyscholar-gptzero-loop.git "$HOME/.agents/skills/bunnyscholar-gptzero-loop"
# Claude Code（当前用户）
git clone https://github.com/Whitopus/bunnyscholar-gptzero-loop.git "$HOME/.claude/skills/bunnyscholar-gptzero-loop"
# Google Antigravity（当前用户）
git clone https://github.com/Whitopus/bunnyscholar-gptzero-loop.git "$HOME/.gemini/config/skills/bunnyscholar-gptzero-loop"
```

- Codex 只装到当前项目时，从项目根目录克隆到 `.agents/skills/bunnyscholar-gptzero-loop`。
- 没有 Git 也可 [下载 ZIP](https://github.com/Whitopus/bunnyscholar-gptzero-loop/archive/refs/heads/main.zip) 并解压到对应目录，确认目录内直接包含 `SKILL.md` 和 `scripts/`。新安装后若当前会话未识别，重新打开会话即可。

进入安装好的 Skill 目录运行快速自检（Windows 若无 `python` 可试 `py -3`，macOS / Linux 试 `python3`；从论文目录运行时改用带引号的脚本绝对路径）：

```sh
python scripts/humanizer_loop.py check-env --quick --summary
```

</details>

<a id="setup-key"></a>

### 🔑 首次登录与配置 Key

1. **登录与建 Key**：第一次用 BunnyScholar？打开 [BunnyScholar 官网](https://bunnyscholar.cn/) 点「登录」微信扫码（若弹出会员推广点「暂不开通」），再到 [密钥管理](https://bunnyscholar.cn/developer/keys) 创建并复制 Key。
2. **一条命令保存**：在 Skill 目录的本地终端运行 `python scripts/humanizer_loop.py setup-key`。已有 Key 会自动复用；缺 Key 时按提示粘贴后直接回车（输入区空白是正常的），脚本保存后会自动读回验证。想主动换 Key 时加 `--replace`。[详细配置与排错](references/onboarding_guide.md)
3. **核对额度**：第一次付费改写前，可在 [查看用量与余额](https://bunnyscholar.cn/developer) 确认赠额与余额，或先用 `--dry-run` 本地估算字数再按需 [充值](https://bunnyscholar.cn/developer/recharge)。`bunnyscholar-api` 技能为选装，CLI 也可直接依据 [官方 API 说明](https://bunnyscholar.cn/skills/bunnyscholar-api.md) 与 [价格](https://bunnyscholar.cn/developer/pricing) 独立运行。

<a id="first-prompt"></a>

### 💬 装好后怎么用？（场景与开场白）

| 你现在想做什么 | 直接复制这句发给 Agent |
| :--- | :--- |
| **改几段英文或中文** | `用 bunnyscholar-gptzero-loop 改下面这段英文，目标 GPTZero，保留术语和引文。先给我候选文本。` |
| **手上已有 GPTZero 报告** | `这是我的 GPTZero 截图。按标记定位 Word 正文，只改第 2 页对应的两段，另存 Word 并标黄。` |
| **整篇 Word 修订并附报告** | `请保留原稿，先用已有报告选段。改完给我 Word 副本，只在最后用 PDF 做一次分页复测并导出 GPTZero PDF 报告。` |
| **登录或换号** | `帮我切换 GPTZero 账号。请把浏览器准备到我可以选账号的位置，我登录好后，你接着对刚才那份 PDF 做复测。` |
| **更新 Skill** | `请更新 bunnyscholar-gptzero-loop，告诉我更新前后的版本。` |

<a id="cli-tools"></a>

### 🧰 命令行用法（可选）

将一段文字保存成 UTF-8 的 `paragraph.txt`，`--dry-run` 会同时估算计费字符数与参考费用（CNY），确认后再执行真实改写（结果在输出 JSON 的 `paragraphs[0].text`）：

```sh
python scripts/humanizer_loop.py humanize --text-file paragraph.txt --dry-run
python scripts/humanizer_loop.py humanize --text-file paragraph.txt --output result.json --allow-quality-warnings
```

默认按英文 GPTZero 处理；中文知网只需追加 `--language zh_CN`（会自动默认 `cnki`）。多段或需对应 Word 段号时改用 `--input paragraphs.json`；每完成一段会自动写入 checkpoint，中途中断可加 `--resume` 续跑以避免重复计费。[JSON 示例与 Word 操作](references/anti_ai_playbook.md)

**保留关键词**。Agent 会先读原文，建议哪些词必须原样保留、哪些可以在复测停滞时逐步放开，再和你简短确认。你已经给了明确要求，或说「你定」，它就直接继续。手动用 CLI 时可传 `--personal-terms "VALORANT,Riot Games"`；在 Windows PowerShell 或术语含逗号/弯撇号 `’` 时推荐改用 `--personal-terms-file terms.json`。 [术语白名单用法](references/anti_ai_playbook.md#personal-terms) · [后续轮次示例](references/anti_ai_playbook.md#loosen-wording)

**复测前核对**。改写结果按段提示数字、单位、否定和限定词的变化。Agent 先看这些变化会不会改掉原意，再判断是否送检。 [候选稿核对](references/anti_ai_playbook.md#review-candidate)

| 命令 | 何时用 |
| :--- | :--- |
| `check-env --quick --summary` | 查看 Python、Key 来源与本地 API 说明。Agent 可省去 `--summary` 读取 JSON。 |
| `setup-key` | 自动复用已有 Key，或在本地终端无回显录入并验证保存结果（默认写入 `~/.env`）。 |
| `review-text --source original.txt --candidate candidate.txt` | 离线核对两份文本中的数字、单位、否定和限定词。 |
| `inspect --docx paper.docx` | 找正文段号、引文、高亮与硬分页。 |
| `apply --docx paper.docx --humanized result.json --output-docx paper.revised.docx` | 按匹配的段号写入选定结果并另存副本（`--humanized` 支持别名 `--input`；自动拦截含图片或脚注/尾注的段落以防丢失）。 |
| `snapshot --docx paper.docx` / `rollback --docx paper.docx --list` | 多轮修订时存档（`--note` 支持别名 `--label`）、查看或恢复版本。 |
| `export-pdf --docx paper.revised.docx` | 用 Windows Word 或 LibreOffice 导出 PDF。 |
| `self-update` / `self-update --apply` | [检查与更新 Skill](#update)。 |

<a id="update"></a>

### 更新 Skill

可以直接对 Agent 说「更新 bunnyscholar-gptzero-loop」，也可以在 Skill 目录运行：

```sh
python scripts/humanizer_loop.py self-update
python scripts/humanizer_loop.py self-update --apply
```

第一条立即查询远端，第二条执行更新。Git 安装沿跟踪分支快进；复制或 ZIP 安装会从同一个 GitHub 归档更新 Skill 自带文件，保留额外文件与本地配置。同版本要补回缺失文件时，复制安装用 `self-update --apply --repair`。已打开的会话若仍沿用旧指引，可让 Agent 重新读取 Skill。

<a id="quick-links"></a>
<a id="troubleshooting"></a>

### 🔧 排错与文档入口

- **密钥已配置，服务仍报错**：自检只看本地来源；`401`/`403` 请核对密钥与控制台状态，`402` 请检查余额。[配置与排错](references/onboarding_guide.md)
- **需要登录或换号**。Agent 可以先打开登录页或账号菜单，再把浏览器交给你扫码、验证或选账号。你操作完，它会核对状态并继续。只换 BunnyScholar 网页账号时，原来的 API Key 可以继续用。 [GPTZero 登录和换号](references/gptzero_browser_sop.md#sign-in-and-switch) · [BunnyScholar 换号](references/onboarding_guide.md#switch-accounts)
- **导出报告无响应**。从 `Scans` 打开对应单文档，再尝试 `Export → Download PDF`。逐页分数可另外记录。 [报告导出](references/gptzero_browser_sop.md#export-report)
- **没装 Word / LibreOffice**：纯文本改写、读取报告和 Word 段落修改都能正常使用，仅从 DOCX 导出 PDF 时需要导出工具。[Word 段落修订与复测](references/anti_ai_playbook.md)
- **Agent 工作流总览**：想查看 Agent 如何按需选择最短路径，见 [SKILL.md](SKILL.md)。

---

<a id="english"></a>

## English

BunnyScholar × GPTZero Loop is a zero-dependency (Python 3.8+ stdlib only) Agent Skill for rewriting selected text with BunnyScholar, reviewing GPTZero results when requested, exporting the native GPTZero PDF report, and applying selected changes to Word.

### ⚡ Fastest Install (Recommended)

> [!IMPORTANT]
> **The easiest way to install is to send this single sentence to any Agent that supports local Skills:**

```text
Install https://github.com/Whitopus/bunnyscholar-gptzero-loop as a Skill and check my setup. Reuse any configured key. If it's missing, open BunnyScholar's sign-in entry, show me where to create a key, and give me the setup command with the full script path.
```

<details>
<summary>Manual Install & Quick Check</summary>

```sh
# Codex (user)
git clone https://github.com/Whitopus/bunnyscholar-gptzero-loop.git "$HOME/.agents/skills/bunnyscholar-gptzero-loop"
# Claude Code (user)
git clone https://github.com/Whitopus/bunnyscholar-gptzero-loop.git "$HOME/.claude/skills/bunnyscholar-gptzero-loop"
# Google Antigravity (user)
git clone https://github.com/Whitopus/bunnyscholar-gptzero-loop.git "$HOME/.gemini/config/skills/bunnyscholar-gptzero-loop"
```

From the installed Skill folder, run `python scripts/humanizer_loop.py check-env --quick --summary` (`py -3` on Windows or `python3` on macOS/Linux).

</details>

### 🔑 Sign In & Configure Key

1. **Sign in**: New to BunnyScholar? Open [BunnyScholar](https://bunnyscholar.cn/), click Log in (WeChat QR), dismiss any membership popup, and create a key under [API Keys](https://bunnyscholar.cn/developer/keys).
2. **Save key**: Run `python scripts/humanizer_loop.py setup-key` in your local terminal (reuses an existing key or prompts with hidden input and saves to `~/.env`; pass `--replace` to rotate).
3. **Check balance**: Review credits at [Usage & Balance](https://bunnyscholar.cn/developer) or [Top up](https://bunnyscholar.cn/developer/recharge) before paid runs. See [Official API Reference](https://bunnyscholar.cn/skills/bunnyscholar-api.md).

### 🧰 Try One Paragraph

```sh
python scripts/humanizer_loop.py humanize --text-file paragraph.txt --dry-run
python scripts/humanizer_loop.py humanize --text-file paragraph.txt --output result.json --allow-quality-warnings
```

English/GPTZero are the defaults. For Word, use `inspect` to locate paragraph IDs and `apply --output-docx` to save a revised copy.

The agent reads the source first and identifies required wording and optional wording it can loosen if later scans stall. It asks about choices that matter unless you have already settled or delegated them. For direct CLI use, pass `--personal-terms "first term,second phrase"`. [Term preservation](references/anti_ai_playbook.md#personal-terms)

The result lists changes in numbers, quantities with units, negations, and qualifiers to review before sending a candidate to the detector. [Candidate review](references/anti_ai_playbook.md#review-candidate)

To sign in or switch accounts, have the agent open the relevant screen, hand it over for verification or account selection, and resume the task when you return control. BunnyScholar's web session and CLI key can be switched independently. [GPTZero sign-in and account switching](references/gptzero_browser_sop.md#sign-in-and-switch) · [BunnyScholar account switching](references/onboarding_guide.md#switch-accounts)

To update, run `self-update` to compare versions, or `self-update --apply` to install. Git installs fast-forward and copied installs use one GitHub archive. Use `--repair` to reinstall the same version on a copied install.

## License

[MIT](LICENSE) · [⬆️ Back to top](#top)
