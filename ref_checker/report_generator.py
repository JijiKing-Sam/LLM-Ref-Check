"""
Markdown报告生成器
"""
from typing import List, Dict, Optional
from datetime import datetime
from .validator import ValidationResult
import logging

logger = logging.getLogger(__name__)


class MarkdownReportGenerator:
    """Markdown格式报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        pass
    
    def generate_report(self, results: List[ValidationResult], 
                       output_path: Optional[str] = None) -> str:
        """
        生成Markdown格式的验证报告
        
        Args:
            results: 验证结果列表
            output_path: 输出文件路径（可选）
            
        Returns:
            Markdown格式的报告字符串
        """
        report_lines = []
        
        # 报告头部
        report_lines.extend(self._generate_header())
        
        # 统计摘要
        report_lines.extend(self._generate_summary(results))
        
        # 详细结果
        report_lines.extend(self._generate_detailed_results(results))
        
        # 报告尾部
        report_lines.extend(self._generate_footer())
        
        report_content = '\n'.join(report_lines)
        
        # 如果指定了输出路径，保存到文件
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                logger.info(f"报告已保存到: {output_path}")
            except Exception as e:
                logger.error(f"保存报告失败: {e}")
        
        return report_content
    
    def _generate_header(self) -> List[str]:
        """生成报告头部"""
        return [
            "# 参考文献验证报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]
    
    def _generate_summary(self, results: List[ValidationResult]) -> List[str]:
        """生成统计摘要"""
        total = len(results)
        valid_count = sum(1 for r in results if r.is_valid)
        suspicious_count = sum(1 for r in results if r.is_suspicious)
        needs_review_count = total - valid_count - suspicious_count
        
        avg_confidence = sum(r.confidence for r in results) / total if total > 0 else 0.0
        
        return [
            "## 📊 验证摘要",
            "",
            f"- **总参考文献数**: {total}",
            f"- **✅ 验证通过**: {valid_count} ({valid_count/total*100:.1f}%)",
            f"- **⚠️ 存在疑问**: {suspicious_count} ({suspicious_count/total*100:.1f}%)",
            f"- **🔍 需要复查**: {needs_review_count} ({needs_review_count/total*100:.1f}%)",
            f"- **平均置信度**: {avg_confidence:.2%}",
            "",
            "---",
            ""
        ]
    
    def _generate_detailed_results(self, results: List[ValidationResult]) -> List[str]:
        """生成详细结果"""
        lines = [
            "## 📋 详细验证结果",
            ""
        ]
        
        for idx, result in enumerate(results, 1):
            lines.extend(self._generate_entry_result(idx, result))
            lines.append("")  # 空行分隔
        
        return lines
    
    def _generate_entry_result(self, index: int, result: ValidationResult) -> List[str]:
        """生成单条参考文献的验证结果"""
        lines = []
        
        # 状态图标
        if result.is_valid:
            status_icon = "✅"
        elif result.is_suspicious:
            status_icon = "⚠️"
        else:
            status_icon = "🔍"
        
        lines.append(f"### {index}. {status_icon} {result.entry.cite_key}")
        lines.append("")
        
        # 基本信息
        lines.append("**基本信息:**")
        lines.append(f"- **标题**: {result.entry.title or '未提供'}")
        lines.append(f"- **作者**: {', '.join(result.entry.authors) if result.entry.authors else '未提供'}")
        lines.append(f"- **年份**: {result.entry.year or '未提供'}")
        if result.entry.journal:
            lines.append(f"- **期刊/会议**: {result.entry.journal}")
        if result.entry.doi:
            lines.append(f"- **DOI**: {result.entry.doi}")
        if result.entry.arxiv_id:
            lines.append(f"- **ArXiv ID**: {result.entry.arxiv_id}")
        lines.append("")
        
        # 验证结果
        lines.append("**验证结果:**")
        lines.append(f"- **状态**: {result.recommendation}")
        lines.append(f"- **置信度**: {result.confidence:.2%}")
        lines.append("")
        
        # 验证源信息
        if result.verification_sources:
            lines.append("**验证源信息:**")
            for source, source_result in result.verification_sources.items():
                if source_result.get('found', False):
                    lines.append(f"- **{source.upper()}**: ✅ 找到匹配")
                    if source_result.get('arxiv_id'):
                        arxiv_id = source_result['arxiv_id']
                        lines.append(f"  - ArXiv ID: [{arxiv_id}](https://arxiv.org/abs/{arxiv_id})")
                    if source_result.get('source_url'):
                        lines.append(f"  - 链接: [{source_result['source_url']}]({source_result['source_url']})")
                    
                    match_details = source_result.get('match_details', {})
                    if match_details:
                        # 基本匹配信息
                        matches = []
                        if match_details.get('title_match'):
                            matches.append("标题匹配")
                        if match_details.get('author_match'):
                            matches.append("作者匹配")
                        if match_details.get('year_match'):
                            matches.append("年份匹配")
                        if matches:
                            lines.append(f"  - 匹配项: {', '.join(matches)}")
                        
                        # 详细验证信息
                        detailed = match_details.get('detailed_validation', {})
                        if detailed:
                            field_validations = detailed.get('field_validations', {})
                            
                            # 标题详细信息
                            if 'title' in field_validations:
                                title_val = field_validations['title']
                                lines.append(f"  - 标题相似度: {title_val.get('similarity', 0):.2%}")
                            
                            # 作者详细信息
                            if 'authors' in field_validations:
                                author_val = field_validations['authors']
                                lines.append(f"  - 作者匹配: {author_val.get('exact_match_count', 0)}个完全匹配, "
                                           f"{author_val.get('partial_match_count', 0)}个部分匹配, "
                                           f"共{author_val.get('total_entry', 0)}个作者")
                                if author_val.get('missing_authors'):
                                    missing = author_val['missing_authors']
                                    if len(missing) <= 3:
                                        lines.append(f"    - ⚠️ 缺失作者: {', '.join(missing)}")
                                    else:
                                        lines.append(f"    - ⚠️ 缺失作者: {', '.join(missing[:3])} 等{len(missing)}个")
                            
                            # 年份详细信息
                            if 'year' in field_validations:
                                year_val = field_validations['year']
                                if not year_val.get('match'):
                                    lines.append(f"  - ⚠️ 年份不匹配: {year_val.get('entry_year')} vs {year_val.get('result_year')}")
                        
                        # 幻觉检测
                        if match_details.get('is_hallucination'):
                            lines.append(f"  - ⚠️ **疑似幻觉引用**")
                        
                        # 问题和警告
                        if match_details.get('issues'):
                            for issue in match_details['issues']:
                                lines.append(f"  - ⚠️ {issue}")
                        if match_details.get('warnings'):
                            for warning in match_details['warnings']:
                                lines.append(f"  - ⚠️ {warning}")
                else:
                    lines.append(f"- **{source.upper()}**: ❌ 未找到匹配")
            lines.append("")
        
        # 问题和警告
        if result.issues:
            lines.append("**❌ 发现的问题:**")
            for issue in result.issues:
                lines.append(f"- {issue}")
            lines.append("")
        
        if result.warnings:
            lines.append("**⚠️ 警告:**")
            for warning in result.warnings:
                lines.append(f"- {warning}")
            lines.append("")
        
        lines.append("---")
        
        return lines
    
    def _generate_footer(self) -> List[str]:
        """生成报告尾部"""
        return [
            "",
            "## 📝 说明",
            "",
            "- ✅ **验证通过**: 在ArXiv等数据源中找到匹配，置信度≥80%",
            "- ⚠️ **存在疑问**: 发现明显问题或未找到匹配",
            "- 🔍 **需要复查**: 置信度较低，建议人工检查",
            "",
            "---",
            "",
            f"*报告由 LLM-Ref-Check 工具生成*"
        ]
