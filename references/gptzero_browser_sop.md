# GPTZero 浏览器操作参考

已有报告、截图或分享链接时，从那份结果开始。新测试用当前宿主可用的浏览器；如果浏览器无法上传或读取文件，用户可以在同一账户自行测试并提供结果。 [GPTZero](https://app.gptzero.me)

## 文本或整篇 PDF

| 目的 | 做法 |
| --- | --- |
| 比较几段文字 | 把需要比较的段落粘贴到 GPTZero 文本框，尽量用相同的输入范围与跟踪到的扫描模式。局部结果只代表该次输入。 |
| 需要分页结果 | 上传匹配当前稿件的 PDF；如果界面提供分页视图，记录页码、分数或标记，并对照 PDF 文本定位 Word 段落。 |
| 卡在段落标黄或付费提示 | 结果视图、可用功能与额度可能因账户而不同。先查看当前的普通扫描或已有结果，可关闭的推广弹窗可直接关闭。 |

某些浏览器中，富文本框经自动填充后字数仍显示零。先聚焦输入框，再用宿主支持的粘贴或文本输入动作。上传路径以宿主浏览器的提示为准，只有上传工具需要文件暂存时才用 `export-pdf --stage-to`。

Codex 内置浏览器实测中，游客页提示文本至少 250 个字符，276 字符样例通过粘贴完成了 `Basic Scan`。实际门槛以页面提示为准。若片段过短，可带上连贯的上下文，并说明分数覆盖的文本范围，或者依照已有报告分析。

## 登录、限制与结果核对

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

## 3. 弹窗处理、免费额度避坑与视图差异

- **鉴别 `Advanced AI Scan` 假 HTTP 429 弹窗与连环广告自动清理**：
  - 实测中 GPTZero 首页右侧 `Advanced AI Scan` 默认锁定勾选且**无法取消**（即使免费账号显示 `0 advanced scans left`），导致点击 `Scan` 或上传后必然并发触发 `POST /v3/ai/text` / `/v3/ai-vocab-scan` HTTP 429 并默认跳入 `Advanced` 标签页，随即弹出**最多 3 连套娃营销弹窗**：
    1. `7 day Free Trial` ➔ 点击右上角 **`×`**；
    2. `Your first year, 30% off`（无 `×`）➔ 点击底部灰字 **`Pass on premium, continue free`**；
    3. `Free chrome extension`（无 `×`）➔ 点击底部 **`Maybe later`**（通用兜底：`Close` / `No thanks` / `Skip` / `Esc`）。
  - **AI Agent 必须自动连环关闭全部垃圾营销弹窗并切回 `Basic Scan`（或 `?scanType=basic`），绝不因此误判为“不可关闭付费阻断”或打扰用户**；只有当 `Basic Scan` 自身报错或免费 credits 归零时，才暂停询问用户换号。
- **PDF 视图 vs Editor 视图差异**：
  - 结果页默认的 **PDF 视图** 会以黄色高亮叠加层直接标出 AI 句子，而 **Editor 视图** 仅按单页展示纯文本、不显示黄色高亮；定位高 AI 句时应结合 PDF 视图高亮与本地 `inspect` 文本。
- **锁定免费检测模式**：日常反复轮测专心使用免费的 **Basic Scan（Model 5.0b）** 与 `Page by page scan`，**默认避开付费 `Advanced` 或 `Hallucination` 标签页**。

---

## 4. 额度耗尽与 HTTP 429 换号询问机制

一旦页面出现以下任一情况：
- 当前账号 `credits` 耗尽；
- 触发 `HTTP 429` 频率或额度阻断；
- 弹出无法关闭的强制升级付费拦截；

Agent **必须立即暂停**，向用户清晰汇报当前剩余额度/报错状态，并**主动询问用户**：
> “当前 GPTZero 账号额度已耗尽或触发限制，请问您是否需要在内置浏览器窗口中退出并切换登录另一个 GPTZero 账号（或改用仅剩的免费模式）？”

若用户选择换号，交由用户在可见窗口手动退出重登（并完成可能出现的新验证码）；用户确认后，Agent 再次通过 `send_message` 复用同一浏览器会话无缝恢复检测。

---

## 5. 终检交付：导出 GPTZero 原生 PDF 报告

- **免费导出原生报告（避开 `/batches/...` 无响应陷阱）**：
  - 注意：上传 PDF 后默认进入的 `/batches/...` 批次页右上角 `Export` / `Share` 按钮可能无响应（no-op）。
  - **正确路径**：点击左侧导航栏 **`Scans`**（`/documents-history`）打开对应文档进入单文档路由 `/documents/<docId>?scanType=basic`，然后点击右上角 **`Export`** ➔ 在 `Download PDF Report` 弹窗点击 **`Download PDF`**，即可免费下载原生 PDF 报告（落盘至浏览器沙箱 `downloads/` 目录）。
- **归档交付**：将 `downloads/` 中新生成的 `GPTZero_*.pdf` 复制归档至用户目标交付目录（建议命名 `<原文件名>_gptzero_report.pdf`），随最终 `.docx` / `.pdf` 一并交付。
- **降级兜底**：若因页面改版或网络异常导致 `Export` 失败，自动降级为附上 **Share 分享链接（单文档 `Share` ➔ 开启 `Link sharing is on`）+ `Basic Scan` 分页截图**，不阻塞最终交付。
