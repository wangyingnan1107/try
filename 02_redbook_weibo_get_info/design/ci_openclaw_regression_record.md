# CI 回归记录：openclaw 安全方案控制片段保留

- 执行时间：2026-03-14
- 运行命令：`python -m unittest discover -s tests -v`
- 关键用例：`test_openclaw_security_text_should_exist_in_final_report`
- 判定标准：聚合报告 `extended_insight` 必须包含“原文证据片段”且命中“安全方案控制”原文。

## 结果摘录

```text
test_openclaw_security_text_should_exist_in_final_report ... ok
test_char_retention_ratio_should_be_at_least_98_percent ... ok
test_keyword_recall_should_be_at_least_95_percent ... ok
...
Ran 6 tests in 0.007s
OK
```

## 结论

在同一条 openclaw 样本帖子上，修复后的聚合链路可稳定输出包含“安全方案控制”原文片段的总结报告，满足回归门禁。
