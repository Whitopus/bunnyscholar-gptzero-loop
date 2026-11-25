# Word 段落修订与复测

## 选段与保留版本

Word 文件可先用 `inspect --docx paper.docx` 查看段落索引、引文、高亮与硬分页。`summary.body_para_indices` 是辅助定位，选段时对照实际文字和报告。PDF 的页码可能随着改写重新分页，因此比较两版时也要比对正文位置。范围由用户指定时，优先保留范围外的内容。用户给出目标值时按其口径记录。

建议将原稿保留，用 `apply --output-docx paper.revised.docx` 另存。如果需要在同一草稿上多轮比较，可用 `snapshot` 留版本。得分未测时省略分数字段，复测后按所测版本记录。`rollback --list` 可查看历史。`--best` 依据已记录的整体 Human 分数；若关注具体页或内容质量，可按 `--version` 恢复选定版本。

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

输入过长时按自然语义切分，改写后合并到原 Word 段号。`humanize` 保存 API 返回的文本与质量提示。要重点保留的术语可用 `--personal-terms`。`--allow-first-person` 适合原本就使用第一人称的文章，`--allow-quality-warnings` 保留提示并让可人工复核的批次正常完成。质量检查默认只评估当次结果，`--max-retries N` 用于显式选择额外改写尝试。`--dual-stage` 会先降重再拟人化，适合用户同时需要两个指标并接受较大改动时。

用 `apply --highlight-paras 6,7` 涂黄整段。要涂黄短语，在供 `apply` 读取的结果 JSON 里为相应段落加入 `"highlight_substrings": ["exact phrase"]`。仅在用户要求清理已有高亮时使用 `--clear-other-highlights`。常见样式和超链接可由脚本保留，改到包含链接、公式、复杂行内样式或引用的段落时，打开交付稿核对。

## 决定是否再做一轮

对照原稿、候选稿和用户提供的反馈，优先处理含义失真、引文丢失或术语被改掉的段落。可能需要调整输入、使用术语表或保留原段落。短尾页或跨页段落导致分数难比较时，先确认报告显示的实际内容再决定是否调整排版。记录版本、实际使用量以及需要用户定夺的取舍。
