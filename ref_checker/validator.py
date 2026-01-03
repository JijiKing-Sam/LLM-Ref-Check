"""
参考文献验证核心逻辑（兼容旧版本）
推荐使用 multi_validator.py 中的 MultiSourceValidator
"""
from typing import List, Dict, Optional
import logging
from .bibtex_parser import BibTeXEntry
from .arxiv_validator import ArXivValidator

# 导入多源验证器
try:
    from .multi_validator import MultiSourceValidator, ValidationResult as MultiValidationResult
    MULTI_SOURCE_AVAILABLE = True
except ImportError:
    MULTI_SOURCE_AVAILABLE = False

logger = logging.getLogger(__name__)


class ValidationResult:
    """单条参考文献的验证结果"""
    
    def __init__(self, entry: BibTeXEntry):
        self.entry = entry
        self.is_valid = False
        self.is_suspicious = False
        self.issues = []
        self.warnings = []
        self.verification_sources = {}
        self.confidence = 0.0
        self.recommendation = "需要人工检查"
    
    def add_issue(self, issue: str):
        """添加问题"""
        self.issues.append(issue)
        self.is_suspicious = True
    
    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append(warning)
    
    def set_verification_source(self, source: str, result: Dict):
        """设置验证源结果"""
        self.verification_sources[source] = result
    
    def calculate_confidence(self):
        """计算置信度"""
        if not self.verification_sources:
            self.confidence = 0.0
            return
        
        # 基于验证源数量和匹配度计算置信度
        total_score = 0.0
        source_count = 0
        
        for source, result in self.verification_sources.items():
            if result.get('found', False):
                source_count += 1
                match_details = result.get('match_details', {})
                similarity = match_details.get('similarity_score', 0.0)
                total_score += similarity
        
        if source_count > 0:
            self.confidence = total_score / source_count
        else:
            self.confidence = 0.0
        
        # 根据置信度设置推荐
        if self.confidence >= 0.8:
            self.recommendation = "验证通过"
            self.is_valid = True
        elif self.confidence >= 0.5:
            self.recommendation = "基本可信，建议复查"
        else:
            self.recommendation = "存在疑问，需要人工检查"
            self.is_suspicious = True
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'cite_key': self.entry.cite_key,
            'title': self.entry.title,
            'authors': self.entry.authors,
            'year': self.entry.year,
            'is_valid': self.is_valid,
            'is_suspicious': self.is_suspicious,
            'confidence': self.confidence,
            'recommendation': self.recommendation,
            'issues': self.issues,
            'warnings': self.warnings,
            'verification_sources': self.verification_sources
        }


class ReferenceValidator:
    """参考文献验证器主类"""
    
    def __init__(self):
        """初始化验证器"""
        self.arxiv_validator = ArXivValidator()
        self.validators = {
            'arxiv': self.arxiv_validator
        }
    
    def validate_entry(self, entry: BibTeXEntry) -> ValidationResult:
        """
        验证单条参考文献
        
        Args:
            entry: BibTeXEntry对象
            
        Returns:
            ValidationResult对象
        """
        result = ValidationResult(entry)
        
        # 基础字段检查
        self._check_basic_fields(entry, result)
        
        # ArXiv验证（CS领域主要使用）
        if entry.arxiv_id or self._is_likely_arxiv_paper(entry):
            arxiv_result = self.arxiv_validator.validate_entry(entry)
            result.set_verification_source('arxiv', arxiv_result)
            
            if not arxiv_result.get('found', False):
                result.add_issue("未在ArXiv中找到匹配的论文")
        
        # 计算最终置信度
        result.calculate_confidence()
        
        return result
    
    def _check_basic_fields(self, entry: BibTeXEntry, result: ValidationResult):
        """检查基本字段完整性"""
        if not entry.title:
            result.add_issue("缺少标题")
        
        if not entry.authors:
            result.add_warning("缺少作者信息")
        
        if not entry.year:
            result.add_warning("缺少年份信息")
        
        # 检查标题是否过于简单（可能是幻觉）
        if entry.title and len(entry.title.split()) < 3:
            result.add_warning("标题过短，可能存在幻觉")
    
    def _is_likely_arxiv_paper(self, entry: BibTeXEntry) -> bool:
        """判断是否可能是ArXiv论文"""
        # CS领域的会议和期刊通常不会在ArXiv
        # 但如果缺少期刊信息，可能是预印本
        if not entry.journal and entry.title:
            return True
        return False
    
    def validate_batch(self, entries: List[BibTeXEntry]) -> List[ValidationResult]:
        """
        批量验证参考文献
        
        Args:
            entries: BibTeXEntry对象列表
            
        Returns:
            ValidationResult对象列表
        """
        results = []
        for entry in entries:
            try:
                result = self.validate_entry(entry)
                results.append(result)
            except Exception as e:
                logger.error(f"验证条目 {entry.cite_key} 时出错: {e}")
                # 创建错误结果
                error_result = ValidationResult(entry)
                error_result.add_issue(f"验证过程出错: {str(e)}")
                results.append(error_result)
        
        return results




