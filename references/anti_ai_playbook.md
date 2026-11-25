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

输入过长时按自然语义切分，改写后合并到原 Word 段号。`humanize` 保存 API 返回的文本与质量提示。`--allow-first-person` 适合原本就使用第一人称的文章，`--allow-quality-warnings` 保留提示并让可人工复核的批次正常完成。质量检查默认只评估当次结果，`--max-retries N` 用于显式选择额外改写尝试。`--dual-stage` 会先降重再拟人化，适合用户同时需要两个指标并接受较大改动时。

用 `apply --highlight-paras 6,7` 涂黄整段。要涂黄短语，在供 `apply` 读取的结果 JSON 里为相应段落加入 `"highlight_substrings": ["exact phrase"]`。仅在用户要求清理已有高亮时使用 `--clear-other-highlights`。常见样式和超链接可由脚本保留，改到包含链接、公式、复杂行内样式或引用的段落时，打开交付稿核对。

<a id="personal-terms"></a>

## 保留术语和关键短语

用 `--personal-terms` 将专名、实验术语或需要保留措辞的短语传给 BunnyScholar 的术语白名单。优先用原文中的写法。BunnyScholar 的接口说明将英文和降重步骤描述为尽量保留，中文拟人改写中的术语、数字和公式由模型处理。 [BunnyScholar API 说明](https://bunnyscholar.cn/skills/bunnyscholar-api.md)

```sh
python scripts/humanizer_loop.py humanize --text-file paragraph.txt --output result.json --personal-terms "VALORANT,Riot Games,twenty-four hours"
```

带逗号的术语用 JSON 字符串数组传入。用 `--dry-run` 可先查看每段命中的 `matched_personal_terms`。改写结果用 `missing_personal_terms` 提示原文中出现、候选中未按相同措辞出现的术语，比较忽略大小写和空白差异。像 `twenty-four hours` 写成 `24 hours` 也会列出，方便结合语义核对。提示本身不会触发付费重试。

## 决定是否再做一轮

先对照原稿与候选稿，特别核对用单词写出的数量、单位、时间间隔，以及「看起来」「可能」等限定。引文序号与术语保留了，原句的断言也可能变强或丢掉细节。`quality_passed` 只表示脚本的几项检查通过。发现失真时可保留原文；需要再试时，可以先把关键短语加入 `--personal-terms`，再结合原文核对一次。

复测尽量用同样的文本范围和扫描模式。整体分数变化后，仍可查看目标页和未改页是否发生变化。短尾页或跨页段落难比较时，先对照实际正文位置。最终记录采用的版本、实测范围、结果和费用。
