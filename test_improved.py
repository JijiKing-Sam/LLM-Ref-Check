#!/usr/bin/env python3
"""
测试改进后的匹配算法
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ref_checker.bibtex_parser import BibTeXParser
from ref_checker.multi_validator import MultiSourceValidator
from ref_checker.improved_matcher import ImprovedMatcher

def test_matcher():
    """测试匹配算法"""
    print("=" * 60)
    print("测试改进的匹配算法")
    print("=" * 60)
    
    # 测试标题相似度
    test_cases = [
        ("Attention is all you need", "Attention Is All You Need", 1.0),
        ("Deep Learning", "Deep learning for computer vision", 0.6),
        ("BERT: Pre-training", "BERT Pre-training of Deep Bidirectional Transformers", 0.7),
    ]
    
    print("\n1. 标题相似度测试:")
    for title1, title2, expected_min in test_cases:
        sim = ImprovedMatcher.calculate_title_similarity(title1, title2)
        status = "✅" if sim >= expected_min else "❌"
        print(f"  {status} '{title1}' vs '{title2}': {sim:.2f} (期望≥{expected_min})")
    
    # 测试作者匹配
    print("\n2. 作者匹配测试:")
    author_tests = [
        (["Vaswani, Ashish", "Shazeer, Noam"], ["Ashish Vaswani", "Noam Shazeer"], True),
        (["Devlin, Jacob"], ["Jacob Devlin", "Ming-Wei Chang"], True),
    ]
    
    for entry_authors, result_authors, should_match in author_tests:
        match, score = ImprovedMatcher.match_authors(entry_authors, result_authors)
        status = "✅" if match == should_match else "❌"
        print(f"  {status} {entry_authors} vs {result_authors}: 匹配={match}, 分数={score:.2f}")
    
    print("\n" + "=" * 60)

def test_validation():
    """测试验证功能"""
    print("\n测试验证功能（使用test_references.bib）")
    print("=" * 60)
    
    test_file = Path(__file__).parent / "test_references.bib"
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    try:
        # 解析
        parser = BibTeXParser()
        entries = parser.parse_file(str(test_file))
        print(f"✅ 解析了 {len(entries)} 条参考文献")
        
        # 验证（只使用Crossref，避免API限制）
        print("\n开始验证（使用Crossref验证器）...")
        validator = MultiSourceValidator(enable_sources=['crossref'])
        
        # 只验证前3条
        test_entries = entries[:3]
        results = validator.validate_batch(test_entries)
        
        print(f"\n验证结果:")
        for i, result in enumerate(results, 1):
            found_count = sum(1 for r in result.verification_sources.values() if r.get('found', False))
            print(f"  {i}. {result.entry.cite_key}")
            print(f"     标题: {result.entry.title[:50]}...")
            print(f"     置信度: {result.confidence:.2%}")
            print(f"     状态: {result.recommendation}")
            print(f"     找到匹配的源: {found_count}/{len(result.verification_sources)}")
            print()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_matcher()
    # test_validation()  # 取消注释以测试实际验证
