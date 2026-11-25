# 新环境冷启动与凭据配置指南（Onboarding Guide）

本指南用于指导 Agent 在全新电脑或零配置环境中，手把手引导新使用者完成 `bunnyscholar-api` 前置安装、`BunnyScholar` API Key 申请、无回显本地持久化、PDF 后端兜底与开工前目标对齐。

---

## 0. 第零步：前置安装 `bunnyscholar-api` 技能

若 `check-env` 报告 `skills.bunnyscholar_api.found` 为 `false`（或需要同步最新线上接口规范），请先执行或引导用户发送以下前置指令：

> **请根据 `https://bunnyscholar.cn/skills/bunnyscholar-api.md`，安装 `bunnyscholar-api`。**

---

## 1. 安全铁律（严禁泄漏密钥）

- **绝对禁止**读取或打印 `~/.env`、项目 `.env` 或插件 `.env` 中的明文内容（严禁 `cat ~/.env`、`printenv`、`echo $BUNNYSCHOLAR_API_KEY`）。
- **绝对禁止**要求用户在聊天框中直接粘贴 `sk-xxxx` 明文 Key，避免密钥进入对话上下文或日志记录。
- 始终先执行静默探针：
  ```bash
  python scripts/humanizer_loop.py check-env --output env_status.json
  ```

---

## 2. 缺失 Key 时的保姆级冷启动引导

当 `env_status.json` 中 `api_key.found` 为 `false` 时，Agent 应按以下 3 步引导用户：

### 第一步：打开 BunnyScholar 开发者控制台
主动调用内置 `browser` Subagent 打开官方控制台：
- 控制台入口：`https://bunnyscholar.cn/developer`
- API Key 管理页：`https://bunnyscholar.cn/developer/keys`
- 充值入口：`https://bunnyscholar.cn/developer/recharge`

礼貌引导用户在可见浏览器窗口中登录账户、领取新用户赠额或按需充值，然后新建一个 `sk-xxxx` 格式的 API Key（**明文仅在创建时展示一次，请立即复制**）。

### 第二步：提供无回显终端命令写入 `~/.env`
将对应系统的无回显命令发给用户，**并明确提醒新手**：
> “在终端里输入或粘贴密钥时，屏幕**不会显示任何字符或星号**，这是正常的安全隐藏机制，粘贴后直接按 `Enter` 即可。”

- **Windows PowerShell**（采用无 BOM UTF-8 写入并自动防行粘连）：
  ```powershell
  $s = Read-Host -Prompt "Enter BUNNYSCHOLAR_API_KEY (typing hidden)" -AsSecureString; $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s); try { $v = [Runtime.InteropServices.Marshal]::PtrToStringAuto($b); $p = Join-Path $HOME ".env"; $enc = [System.Text.UTF8Encoding]::new($false); $pre = if ((Test-Path $p) -and ([System.IO.File]::ReadAllText($p) -notmatch "(\r?\n)$")) { "`n" } else { "" }; [System.IO.File]::AppendAllText($p, "${pre}BUNNYSCHOLAR_API_KEY=$v`n", $enc); Write-Host "Saved to $p" } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
  ```

- **macOS / Linux Bash / Zsh**：
  ```bash
  read -rsp "Enter BUNNYSCHOLAR_API_KEY (typing hidden): " k && echo "" && printf 'BUNNYSCHOLAR_API_KEY=%s\n' "$k" >> ~/.env && unset k && echo "Saved."
  ```

### 第三步：复跑探针确认就绪
用户回复“已配置”后，再次运行 `check-env` 确认 `api_key.found` 为 `true`。

---

## 3. 无 Word / LibreOffice 兜底与余额不足（HTTP 402）引导

- **若 `word_com` 与 `libreoffice` 均不可用**：
  - 明确告知用户**不影响核心降 AI 功能**——可直接走 GPTZero 首页**纯文本框粘贴快测**；若需要整篇 PDF 分页检测，可引导用户按需安装免费开源的 [LibreOffice](https://www.libreoffice.org/) 后再试 `export-pdf`。
- **若调用 `humanize` 遇到 HTTP 402（`insufficient_balance`）**：
  - 立即暂停并附上充值链接 `https://bunnyscholar.cn/developer/recharge`（拟人改写参考单价约 ¥1 / 千计费字符，英文约 3 个字符计 1 单位），请用户小额充值后回复确认即可无缝继续。

---

## 4. 开工前 1 轮极简目标对齐

正式开改前，用 1 句话轻问用户以下 3 项偏好（若用户已在首句说明或希望按默认，直接推进，不啰嗦）：
1. **期望达标线**：总体/每页希望 AI 率低于多少（默认 `Human >= 85%` / `AI <= 15%`）？
2. **第一人称限制**：是否禁止出现 `I/we/our`（反思或工科论文可开启 `--allow-first-person`）？
3. **Word 高亮要求**：是否需要为修订段落或局部短语施加黄色荧光笔高亮？
