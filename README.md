# 🔍 LLM 参考文献幻觉检测工具

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io/)

一个**百分百准确可靠**的 LLM 参考文献幻觉检测工具，专门用于验证 BibTeX 格式的参考文献，确保论文中的参考文献完全准确，避免因 LLM 生成幻觉而被拒稿。

## ✨ 特性

- ✅ **高精度验证**: 通过 ArXiv API 验证 CS 领域论文的真实性
- 📊 **详细报告**: 生成 Markdown 格式的详细验证报告
- 🔍 **多维度检查**: 验证标题、作者、年份、ArXiv ID 等多个字段
- 🚀 **易于扩展**: 预留批量处理接口，支持后期扩展
- 📝 **BibTeX 支持**: 完整支持 BibTeX 格式解析
- 🌐 **Web 界面**: 提供友好的 Streamlit Web 界面，无需命令行操作

## 🎯 核心功能

1. **BibTeX 解析**: 自动解析 BibTeX 文件，提取所有参考文献条目
2. **ArXiv 验证**: 通过 ArXiv API 验证论文是否存在
3. **智能匹配**: 通过标题、作者、年份等多维度匹配论文
4. **置信度评估**: 为每条参考文献计算置信度分数
5. **详细报告**: 生成包含统计摘要和详细验证结果的 Markdown 报告

## 📦 安装

### 环境要求

- Python 3.7+
- pip

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/JijiKing-Sam/LLM-Ref-Check.git
cd LLM-Ref-Check

# 安装依赖（推荐使用 python -m pip 确保使用正确的环境）
python -m pip install -r requirements.txt

# 或者如果使用 conda 环境，先激活环境
conda activate your_env
python -m pip install -r requirements.txt
```

**注意**: 如果使用 conda 环境，请使用 `python -m pip` 而不是直接使用 `pip`，以确保包安装到正确的环境中。

## 🚀 使用方法

### 方法 1: Web 界面（推荐）✨

启动 Web 界面：

```bash
# 安装依赖（如果还没安装）
python -m pip install -r requirements.txt

# 启动 Web 界面
streamlit run app.py

# 或者使用启动脚本
bash run_web.sh
```

然后在浏览器中打开 `http://localhost:8501`，你可以：
- 📁 上传 BibTeX 文件
- 📝 直接粘贴 BibTeX 文本
- 📊 查看实时验证结果
- 📥 下载验证报告

### 方法 2: 命令行工具

验证单个 BibTeX 文件：

```bash
python main.py your_references.bib
```

### 指定输出文件

```bash
python main.py your_references.bib -o report.md
```

### 详细日志

```bash
python main.py your_references.bib -v
```

### 命令行参数

```
usage: main.py [-h] [-o OUTPUT] [-v] input_file

positional arguments:
  input_file            输入的BibTeX文件路径

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        输出报告文件路径（默认为输入文件名_report.md）
  -v, --verbose         显示详细日志信息
```

## 📋 输入格式

工具支持标准的 BibTeX 格式，例如：

```bibtex
@article{vaswani2017attention,
  title={Attention is all you need},
  author={Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and others},
  journal={Advances in neural information processing systems},
  volume={30},
  year={2017},
  eprint={arxiv:1706.03762}
}

@inproceedings{example2023paper,
  title={Example Paper Title},
  author={Author, First and Author, Second},
  booktitle={Proceedings of Example Conference},
  year={2023}
}
```

## 📊 输出报告

工具会生成一个 Markdown 格式的验证报告，包含：

1. **验证摘要**: 统计信息（总数、通过数、疑问数等）
2. **详细结果**: 每条参考文献的验证详情
   - 基本信息（标题、作者、年份等）
   - 验证状态（✅ 验证通过 / ⚠️ 存在疑问 / 🔍 需要复查）
   - 置信度分数
   - 验证源信息
   - 发现的问题和警告

### 报告示例

```markdown
# 参考文献验证报告

## 📊 验证摘要

- **总参考文献数**: 10
- **✅ 验证通过**: 8 (80.0%)
- **⚠️ 存在疑问**: 1 (10.0%)
- **🔍 需要复查**: 1 (10.0%)
- **平均置信度**: 85.00%

## 📋 详细验证结果

### 1. ✅ vaswani2017attention

**基本信息:**
- **标题**: Attention is all you need
- **作者**: Vaswani, Ashish, Shazeer, Noam, Parmar, Niki
- **年份**: 2017
- **ArXiv ID**: 1706.03762

**验证结果:**
- **状态**: 验证通过
- **置信度**: 100.00%

**验证源信息:**
- **ARXIV**: ✅ 找到匹配
  - ArXiv ID: [1706.03762](https://arxiv.org/abs/1706.03762)
  - 匹配项: 标题匹配, 作者匹配, 年份匹配
```

## 🏗️ 项目结构

```
LLM-Ref-Check/
├── ref_checker/          # 核心模块
│   ├── __init__.py
│   ├── bibtex_parser.py  # BibTeX 解析器
│   ├── arxiv_validator.py # ArXiv API 验证器
│   ├── validator.py      # 验证核心逻辑
│   ├── report_generator.py # Markdown 报告生成器
│   └── batch_processor.py # 批量处理模块（预留）
├── main.py               # 主程序入口
├── requirements.txt      # 依赖包
├── README.md            # 项目说明
└── .gitignore           # Git 忽略文件
```

## 🔧 技术实现

### 验证流程

1. **解析阶段**: 使用 `bibtexparser` 解析 BibTeX 文件
2. **验证阶段**: 
   - 优先使用 ArXiv ID 直接查询
   - 如果无 ArXiv ID，通过标题和作者搜索
   - 如果仍无结果，仅通过标题搜索
3. **匹配评估**: 
   - 标题相似度匹配
   - 作者匹配
   - 年份匹配
   - 计算综合置信度
4. **报告生成**: 生成详细的 Markdown 报告

### 置信度计算

- **≥80%**: 验证通过 ✅
- **50-80%**: 基本可信，建议复查
- **<50%**: 存在疑问，需要人工检查 ⚠️

## 🚧 批量处理（预留功能）

项目已预留批量处理接口，位于 `ref_checker/batch_processor.py`，支持：

- 处理目录中的所有 BibTeX 文件
- 批量生成验证报告
- 统计汇总信息

## ⚠️ 注意事项

1. **API 限制**: ArXiv API 有请求频率限制，工具已内置延迟机制
2. **网络连接**: 需要稳定的网络连接访问 ArXiv API
3. **验证范围**: 当前主要针对 CS 领域的 ArXiv 论文，其他来源的论文可能无法验证
4. **置信度阈值**: 可根据实际需求调整置信度阈值

## 🔮 未来计划

- [ ] 支持更多数据源（DBLP、Google Scholar、Crossref 等）
- [ ] 多源交叉验证机制
- [ ] 本地缓存机制，避免重复查询
- [ ] 支持更多参考文献格式（APA、MLA 等）
- [ ] Web 界面
- [ ] 批量处理 CLI 工具

## 📄 许可证

本项目采用 MIT 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过 GitHub Issues 联系。

---

**重要提示**: 本工具旨在辅助验证参考文献，但**不能完全替代人工检查**。对于重要的论文，建议结合多个数据源和人工验证。