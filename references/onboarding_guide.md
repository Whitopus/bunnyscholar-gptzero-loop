# 初次配置与排错

**第一次用 BunnyScholar，先登录账户。** Agent 有浏览器控制时，直接打开官网、点「登录」，确认微信扫码弹窗出现，再请用户扫码。也可以自行用同一入口登录。用户说「扫完了」后，接回原会话确认落地页。如果出现会员推广，点「暂不开通」，再通过首页「开放平台」进入控制台。此时可以直接准备后面的终端命令。 [BunnyScholar 官网](https://bunnyscholar.cn/)

**以前配过 Key，或者不确定配过没有？** 在 Skill 目录里运行下面这行。Windows 可把 `python` 换成 `py -3`，macOS / Linux 常用 `python3`。如果当前目录是论文目录，请用脚本的绝对路径。

```sh
python scripts/humanizer_loop.py check-env --quick --summary
```

探针报告密钥来源和本地 API 文档是否找到。它不会打开 Word、连接服务或产生改写扣费。输出为 `found` 时，可以复用已有配置。对 Agent 而言，缺本地 `bunnyscholar-api` 文件只意味着需要打开官方接口说明。可选的本地安装可以使用同一份文档。 [BunnyScholar 官方 API 说明](https://bunnyscholar.cn/skills/bunnyscholar-api.md)

## 密钥缺失或需要更新

1. 在开放平台的左侧菜单打开「API Keys」。从首页点「开放平台」若打开了新标签页，切到新标签页继续。有可用的本地 Key 就复用。没有的话，Agent 可以打开密钥页，填写易辨识的名称（如 `Codex`），并提前给出带完整路径的终端命令。由用户点击「创建 Key」并复制新密钥，直接粘贴到下一步的本地终端。控制台提示只显示一次时，也可以先存到本地密码管理器。 [密钥管理](https://bunnyscholar.cn/developer/keys)
2. 在**自己的本地终端**执行下面的命令。出现提示后粘贴密钥，输入区保持空白是正常的，直接按 Enter。Agent 可先把实际脚本路径填好，用户只负责粘贴密钥。

   ```sh
   python scripts/humanizer_loop.py setup-key
   ```

3. 看到 `Using the existing BunnyScholar key …` 或 `Saved and verified the local key …` 就已完成本地配置。`setup-key` 默认复用现有 Key，缺失时才录入。想更新就加 `--replace`。默认保存到 `~/.env`，会替换旧的同名条目并保留其他配置。进程环境里的旧 Key 会优先于文件。更新文件后如果快检仍显示 `env:BUNNYSCHOLAR_API_KEY`，请同步更新或清除旧的环境变量，再开新终端或重启 Agent。

`setup-key --env-file /path/to/.env` 可自选保存位置。用 `check-env --env-paths /path/to/.env` 和 `humanize --env-paths /path/to/.env` 让两处读取同一个文件。远程 Agent 或云端工作区应在其运行环境配置 `BUNNYSCHOLAR_API_KEY`，本机文件和浏览器会话通常由各环境分别管理。

第一次用 Key 改写前，可以看一下开放平台的「用量信息」。赠额和余额够用就可以继续。整篇或多轮处理时可用 `humanize --dry-run` 先看估算计费字符，再对照服务单价决定是否充值。 [查看用量与余额](https://bunnyscholar.cn/developer) · [价格](https://bunnyscholar.cn/developer/pricing) · [充值入口](https://bunnyscholar.cn/developer/recharge)

<a id="switch-accounts"></a>

## 换账户时

- **只换网页账户。** Agent 可以先打开账号菜单，把浏览器准备到切换账户或重新登录的位置。请用户用目标账户扫码或选择账户，返回后核对网页账户并继续原任务。已有的 CLI 凭据继续按原配置使用。
- **付费 API 也要换账户。** 在目标账户的「API Keys」准备好对应的 Key，用 `setup-key --replace` 更新本地文件。接着用 `check-env --quick --summary` 核对实际读取来源。如果旧 Key 还设在当前进程的环境变量里，请先更新或清除旧变量，再重启受影响的终端或 Agent。自检只显示来源，账户归属用用户在控制台确认的 Key 对应关系来核对。

## 遇到什么，下一步做什么

| 看到的情况 | 下一步 |
| --- | --- |
| 找不到 Python 或脚本 | Windows 试 `py -3 --version`，macOS/Linux 试 `python3 --version`。在安装目录执行命令，或让 Agent 给出带引号的完整脚本路径。 |
| `setup-key` 提示需要本地终端 | 用自己能输入的 PowerShell、终端或 Terminal，运行 Agent 给出的命令。密钥输入是交互步骤，聊天里只需回复配置状态。 |
| 本地找到 Key，API 返回 `401` / `403` | 核对自检命中的来源，到控制台确认密钥状态。 |
| BunnyScholar 返回 `402` | 余额不足，可在控制台查看赠额和余额。需要充值时由用户操作。 [充值入口](https://bunnyscholar.cn/developer/recharge) |
| API 提示输入过长或过短 | 用 `humanize --dry-run` 看计费长度。每次请求需要 20–500 个计费字符。 |
| 只需纯文本，或者已经有可扫描的 PDF | 可直接继续。只有需要从 Word 导出 PDF 时，才需要 Word 或 LibreOffice。 |
| 想检查 PDF 导出 | 运行 `check-env --summary --skip-update-check`。若自动导出不可用，可在 Word 中手动另存为 PDF、安装 LibreOffice，或在无需分页时改用文本扫描。 |

版本更新与配置可以各自进行。用 `self-update` 检查版本，或直接执行 `self-update --apply` 更新。复制安装缺文件可用 `self-update --apply --repair` 重装同版本。详见 [更新 Skill](../README.md#update)。
