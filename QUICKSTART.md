# 快速开始指南

## 5分钟快速上手

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备你的BibTeX文件

将你的参考文献保存为 `.bib` 文件，例如 `my_references.bib`

### 3. 运行验证

```bash
python main.py my_references.bib
```

### 4. 查看报告

工具会自动生成 `my_references_report.md` 文件，包含详细的验证结果。

## 示例

项目包含一个示例文件 `example.bib`，你可以用它来测试：

```bash
python main.py example.bib
```

## 测试工具

运行测试脚本确保工具正常工作：

```bash
python test_example.py
```

## 常见问题

### Q: 为什么有些论文验证失败？

A: 可能的原因：
1. 论文不在 ArXiv 上（例如发表在期刊或会议上的论文）
2. 标题或作者信息不完整
3. 网络连接问题

### Q: 如何提高验证准确率？

A: 建议：
1. 确保 BibTeX 条目包含完整的标题、作者和年份
2. 如果论文在 ArXiv 上，添加 `eprint={arxiv:XXXX.XXXXX}` 字段
3. 对于非 ArXiv 论文，当前版本可能无法验证（未来版本会支持更多数据源）

### Q: 可以批量处理多个文件吗？

A: 当前版本支持单文件处理。批量处理功能已在 `ref_checker/batch_processor.py` 中预留，可以自行扩展使用。

## 下一步

- 查看 [README.md](README.md) 了解完整功能
- 查看生成的报告了解验证结果
- 根据需要调整置信度阈值（在 `ref_checker/validator.py` 中）



