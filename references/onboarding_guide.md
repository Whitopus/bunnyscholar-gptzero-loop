# 新环境冷启动与凭据配置指南（Onboarding Guide）

本指南用于指导 Agent 在全新电脑或未配置环境中，安全完成 `bunnyscholar-api` 前置安装、`BunnyScholar` API Key 申请、无回显本地持久化与后端环境校验。

---

## 0. 第零步：前置安装 `bunnyscholar-api` 技能

若 `check-env` 报告 `skills.bunnyscholar_api.found` 为 `false`（或需要同步最新线上接口规范），请先执行以下前置安装指令：

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

## 2. 缺失 Key 时的冷启动引导流程

当 `env_status.json` 中 `api_key.found` 为 `false` 时，Agent 应按以下步骤引导用户：

### 第一步：打开 BunnyScholar 开发者控制台
主动调用内置 `browser` Subagent 打开官方控制台：
- 控制台入口：`https://bunnyscholar.cn/developer`
- API Key 管理页：`https://bunnyscholar.cn/developer/keys`
- 充值入口：`https://bunnyscholar.cn/developer/recharge`

礼貌引导用户在可见浏览器窗口中登录账户、领取新用户赠额或完成充值，然后新建一个 `sk-xxxx` 格式的 API Key（**明文仅在创建时展示一次，请立即复制**）。

### 第二步：提供无回显终端命令写入 `~/.env`
请用户在本地终端执行以下对应系统的无回显命令（输入时屏幕不会显示字符）：

- **Windows PowerShell**：
  ```powershell
  $k = Read-Host -Prompt "Enter BUNNYSCHOLAR_API_KEY (typing hidden)" -AsSecureString; $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($k)); Add-Content -Path "$HOME\.env" -Value "BUNNYSCHOLAR_API_KEY=$plain"; Remove-Variable k, plain; Write-Output "Saved."
  ```

- **macOS / Linux Bash / Zsh**：
  ```bash
  read -rsp "Enter BUNNYSCHOLAR_API_KEY (typing hidden): " k && echo "" && printf 'BUNNYSCHOLAR_API_KEY=%s\n' "$k" >> ~/.env && unset k && echo "Saved."
  ```

### 第三步：复跑探针确认就绪
用户回复“已配置”后，再次运行：
```bash
python scripts/humanizer_loop.py check-env --output env_status.json
```
确认 `api_key.found` 为 `true`、`pdf_backends` 至少有一项可用（Windows 优先 `word_com`，跨平台兜底 `libreoffice`），即可进入正式论文处理闭环。
