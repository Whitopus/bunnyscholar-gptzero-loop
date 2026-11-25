# GPTZero 内置浏览器自检标准作业程序（Browser SOP）

本指南规范 Agent 如何驱动内置 `browser` Subagent 在 `https://app.gptzero.me` 安全、稳定地完成 PDF 分页 AI 检测。

---

## 0. 已有报告优先原则（不浪费 Credits）

若用户已经直接提供了 GPTZero 分享链接（如 `?scanType=bibliography_scan` 等结果页）或检测报告截图，**优先直接读取并分析已有结果**，无需强制从零重新上传扫描，避免重复消耗 credits。

---

## 1. 导出并暂存 PDF

在启动浏览器上传前，使用 `export-pdf` 生成带完整超链接与黄色高亮的 PDF，并一键暂存至内置浏览器沙箱的 `uploads/` 目录：
```bash
python scripts/humanizer_loop.py export-pdf --docx paper.docx --stage-to "<ArtifactDir>/browser_sandbox/uploads" --output pdf_res.json
```
> 注：向 `browser` Subagent 传递上传文件名时，仅传单段文件名（如 `paper.pdf`），由其在沙箱 `uploads/` 目录内读取上传。

---

## 2. 登录护航与人机校验安全红线

1. **打开检测页**：驱动内置 `browser` Subagent 访问 `https://app.gptzero.me`。
2. **严禁绕过任何安全或人机校验**：
   - 一旦页面要求登录，或触发 **hCaptcha / Cloudflare Turnstile** 等“验证您是人类”拦截，Agent **必须立即停止操作并暂停**。
   - 礼貌引导用户在可见的内置浏览器窗口中手动登录账号并完成人机验证。
   - **提示用户登录免费账号的价值**：登录免费 GPTZero 账号通常即可获得 **10,000 credits** 以及最关键的 **`Page by page scan`（逐页分页评分）**，稳定性和信息量远高于未登录游客模式。
3. **复用同一个浏览器会话**：
   - 当用户完成登录与验证并回复确认后，Agent **必须通过 `send_message` 复用同一个已保留 Cookie 的 `browser` Subagent 会话**接手后续上传与检测，切勿新开无 Cookie 的 `browser` 实例。

---

## 3. 弹窗处理与免费额度避坑规范

- **可安全关闭的普通弹窗**：页面内的普通营销推广、会员试用弹窗（含 `×` 或 `Close` 按钮）可直接点击关闭，继续检测流程。
- **锁定免费检测模式**：
  - 上传文件并启动扫描时，日常反复轮测专心使用免费的 **Basic Scan（Model 5.0b）** 并展开查看 **`Page by page scan`** 分页得分。
  - **默认避开付费标签页**：不要点击容易触发配额限制或 `HTTP 429` 弹窗的付费 **`Advanced`** 或 **`Hallucination`** 标签页。

---

## 4. 额度耗尽与 HTTP 429 换号询问机制

一旦页面出现以下任一情况：
- 当前账号 `credits` 耗尽；
- 触发 `HTTP 429` 频率或额度阻断；
- 弹出无法关闭的强制升级付费拦截；

Agent **必须立即暂停**，向用户清晰汇报当前剩余额度/报错状态，并**主动询问用户**：
> “当前 GPTZero 账号额度已耗尽或触发限制，请问您是否需要在内置浏览器窗口中退出并切换登录另一个 GPTZero 账号（或改用仅剩的免费模式）？”

若用户选择换号，交由用户在可见窗口手动退出重登（并完成可能出现的新验证码）；用户确认后，Agent 再次通过 `send_message` 复用同一浏览器会话无缝恢复检测。
