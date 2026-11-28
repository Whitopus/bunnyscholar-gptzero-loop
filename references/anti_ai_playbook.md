# Word 段落修订与复测

## 选段与保留版本

Word 文件可先用 `inspect --docx paper.docx` 查看段落索引、引文、高亮与硬分页。`summary.body_para_indices` 是辅助定位，选段时对照实际文字和报告。PDF 的页码可能随着改写重新分页，因此比较两版时也要比对正文位置。范围由用户指定时，优先保留范围外的内容。用户给出目标值时按其口径记录。

建议将原稿保留，用 `apply --output-docx paper.revised.docx` 另存。多轮比较可以固定一份工作副本，用 `snapshot` 为它存原版和各轮候选；默认每个 Word 文件有独立的快照历史。得分未测时省略分数字段，复测后按所测版本记录。`rollback --list` 可查看历史。`--best` 只比较整体 Human 分数，同分优先较新的快照。若本轮事实有误、只改善了另一项分数或已知道要保留哪版，按 `--version` 恢复选定版本。

## 段落输入与高亮

```json
{
  "paragraphs": [
    {
      "para_index": 6,
      "text": "Use the text of the selected paragraph here."
    }
  ]
}
```

输入过长时按自然语义切分，改写后合并到原 Word 段号。`humanize` 保存 API 返回的文本与质量提示。`--allow-first-person` 适合原本就使用第一人称的文章，`--allow-quality-warnings` 保留提示并让可人工复核的批次正常完成。质量检查默认只评估当次结果，`--max-retries N` 用于显式选择额外改写尝试。`--dual-stage` 会先降重再拟人化（同等计费字符），当单阶段改写被 GPTZero 识别为 `AI Paraphrased` 时，直接切换 `--dual-stage` 通常比反复单阶段更有效。

用 `apply --highlight-paras 6,7` 涂黄整段。要涂黄短语，在供 `apply` 读取的结果 JSON 里为相应段落加入 `"highlight_substrings": ["exact phrase"]`。仅在用户要求清理已有高亮时使用 `--clear-other-highlights`。常见样式和超链接可由脚本保留，改到包含链接、公式、复杂行内样式或引用的段落时，打开交付稿核对。

<a id="personal-terms"></a>

## 保留术语和关键短语

Agent 先读本轮要改的原文和已有报告，自己挑出必须原样保留的名称和术语，以及首轮可暂时保留、后续能放松的短语。重要数字、单位和限定条件可以记下来做语义核对。把会影响改写的建议集中说清楚，留给用户一次确认或调整的机会。例如：

> 我建议原样保留 `VALORANT` 和 `Riot Games`。首轮也可以保留 `twenty-four hours`，如果复测卡住，我会允许写成 `24 hours`，并核对「每 24 小时刷新」这条事实。这样可以吗？

用户已经给了明确的要求，或者让 Agent 自己定，就按授权继续。明确要求原样保留的词在后续轮次继续保留。其余措辞可以在已商定的范围内调整。

用 `--personal-terms` 将专名、实验术语或需要保留措辞的短语传给 BunnyScholar 的术语白名单。优先用原文中的写法。BunnyScholar 的接口说明将英文和降重步骤描述为尽量保留，中文拟人改写中的术语、数字和公式由模型处理。 [BunnyScholar API 说明](https://bunnyscholar.cn/skills/bunnyscholar-api.md)

```sh
python scripts/humanizer_loop.py humanize --text-file paragraph.txt --output result.json --personal-terms "VALORANT,Riot Games,twenty-four hours"
```

带逗号、引号或英文弯撇号 `’` 的术语（尤其在 Windows PowerShell 中）推荐改用 `--personal-terms-file terms.json`（UTF-8 JSON 数组或每行一条的纯文本，支持 `#` 注释），避免命令行引号转义报错。用 `--dry-run` 可先查看每段命中的 `matched_personal_terms`。改写结果用 `missing_personal_terms` 提示原文中出现、候选中未按相同措辞出现的术语，比较忽略大小写和空白差异。像 `twenty-four hours` 写成 `24 hours` 也会列出，方便结合语义核对。提示本身不会触发付费重试。

<a id="review-candidate"></a>

## 候选稿送检前怎么核对

`humanize` 在每段结果里附上 `fidelity_warnings`，分别列出数字、有单位的数值、否定词和限定词在原文与候选中的增减。例如 `0.2 V` 变成 `0.2 °C` 会标出数量单位对的变化，`did not` 或 `may` 消失也会提示。常见等义写法如 `twenty-four hours` 和 `24 h` 按同一数值和单位比较。提示只用于复核，不会自动重试。

Agent 对照原句判断变化是否影响结论，再决定是否值得送检。数字和关键词全保留时，也要检查它们仍指向同一对象，尤其是否定范围、因果强度和引文。手上已有候选时，把同一段原文和候选各存一份 UTF-8 文本，即可离线核对。

```sh
python scripts/humanizer_loop.py review-text --source original.txt --candidate candidate.txt
```

<a id="loosen-wording"></a>

## 后续轮次怎么放宽

如果同范围复测没有进展，或者候选因为固定措辞读起来生硬，可以下一轮先从白名单移出一两项允许调整的短语，再考虑放开句式或段内组织。每轮按实际问题决定改多少。比如移出 `twenty-four hours` 后，`24 hours` 可以接受；删掉刷新间隔或改成「几乎每天」会改变原来的信息。

另存候选，再对照原稿与上一版可用候选。核对数量、单位、时间间隔、引文，以及「看起来」「可能」等限定。`quality_passed` 只表示脚本的几项检查通过。候选丢了事实或改了用户要求原样保留的词，就保留上一版可用候选或原文。继续放宽会影响明确要求、超出授权范围或预算时，再和用户讨论。

多轮迭代建议采用「冻结已过关段落 + 局部纯文本试跑 + 终稿整篇 PDF 一次终验」策略：先冻结已达标的段落，仅粘贴待改段落做纯文本复测，确认过关后再导出整篇 PDF 做唯一一次终验，可大幅节省扫描额度。最终记录采用的版本、实测范围、结果和费用。
