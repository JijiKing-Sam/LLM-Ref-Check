#!/usr/bin/env python3
"""
简单的测试脚本，用于验证工具是否正常工作
"""
import sys
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ref_checker.bibtex_parser import BibTeXParser
from ref_checker.validator import ReferenceValidator
from ref_checker.report_generator import MarkdownReportGenerator

def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("LLM参考文献幻觉检测工具 - 功能测试")
    print("=" * 60)
    
    # 测试文件路径
    test_file = project_root / "example.bib"
    
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        print("请先创建 example.bib 文件")
        return False
    
    try:
        # 1. 测试解析
        print("\n[1/3] 测试 BibTeX 解析...")
        parser = BibTeXParser()
        entries = parser.parse_file(str(test_file))
        print(f"✅ 成功解析 {len(entries)} 条参考文献")
        
        # 显示解析结果
        for i, entry in enumerate(entries[:3], 1):  # 只显示前3条
            print(f"  {i}. {entry.cite_key}: {entry.title[:50]}...")
        
        # 2. 测试验证（只验证第一条，避免API限制）
        print("\n[2/3] 测试参考文献验证...")
        print("⚠️  注意: 为了节省API调用，只验证第一条参考文献")
        validator = ReferenceValidator()
        if entries:
            result = validator.validate_entry(entries[0])
            print(f"✅ 验证完成")
            print(f"   - 状态: {result.recommendation}")
            print(f"   - 置信度: {result.confidence:.2%}")
            if result.verification_sources:
                for source, source_result in result.verification_sources.items():
                    found = source_result.get('found', False)
                    status = "✅ 找到" if found else "❌ 未找到"
                    print(f"   - {source.upper()}: {status}")
        
        # 3. 测试报告生成
        print("\n[3/3] 测试报告生成...")
        if entries:
            # 只验证前2条用于测试
            test_entries = entries[:2]
            results = validator.validate_batch(test_entries)
            report_generator = MarkdownReportGenerator()
            report_content = report_generator.generate_report(results)
            print(f"✅ 报告生成成功 (长度: {len(report_content)} 字符)")
            print(f"   报告包含 {len(report_content.split(chr(10)))} 行")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！工具可以正常使用。")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_basic_functionality()
    sys.exit(0 if success else 1)




