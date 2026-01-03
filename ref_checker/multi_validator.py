"""
多源验证器
整合 ArXiv、Crossref、OpenReview、Google Scholar 等多个数据源
实现交叉验证逻辑
"""
from typing import List, Dict, Optional
import logging
from .bibtex_parser import BibTeXEntry
from .arxiv_validator import ArXivValidator
from .crossref_validator import CrossrefValidator
from .openreview_validator import OpenReviewValidator
from .scholar_validator import ScholarValidator

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
        self.source_count = 0  # 找到匹配的源数量
    
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
        if result.get('found', False):
            self.source_count += 1
    
    def calculate_confidence(self):
        """计算置信度（基于多源交叉验证）"""
        if not self.verification_sources:
            self.confidence = 0.0
            return
        
        # 统计找到匹配的源数量
        found_sources = sum(1 for r in self.verification_sources.values() if r.get('found', False))
        total_sources = len(self.verification_sources)
        
        if found_sources == 0:
            self.confidence = 0.0
        elif found_sources == 1:
            # 只有一个源找到，置信度较低
            source_result = next(r for r in self.verification_sources.values() if r.get('found', False))
            match_details = source_result.get('match_details', {})
            similarity = match_details.get('similarity_score', 0.0)
            self.confidence = similarity * 0.7  # 单源验证降低置信度
        elif found_sources >= 2:
            # 多个源找到，计算平均相似度并提高置信度
            total_similarity = 0.0
            for source, source_result in self.verification_sources.items():
                if source_result.get('found', False):
                    match_details = source_result.get('match_details', {})
                    similarity = match_details.get('similarity_score', 0.0)
                    total_similarity += similarity
            
            avg_similarity = total_similarity / found_sources
            # 多源验证提高置信度
            self.confidence = min(avg_similarity * (1.0 + 0.2 * (found_sources - 1)), 1.0)
        else:
            self.confidence = 0.0
        
        # 根据置信度和源数量设置推荐
        if self.confidence >= 0.8 and found_sources >= 2:
            self.recommendation = "验证通过（多源确认）"
            self.is_valid = True
        elif self.confidence >= 0.8:
            self.recommendation = "验证通过"
            self.is_valid = True
        elif self.confidence >= 0.6 and found_sources >= 2:
            self.recommendation = "基本可信（多源确认）"
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
            'source_count': self.source_count,
            'issues': self.issues,
            'warnings': self.warnings,
            'verification_sources': self.verification_sources
        }


class MultiSourceValidator:
    """多源验证器主类"""
    
    def __init__(self, enable_sources: Optional[List[str]] = None):
        """
        初始化多源验证器
        
        Args:
            enable_sources: 启用的验证源列表，None表示启用所有
                可选值: 'arxiv', 'crossref', 'openreview', 'scholar'
        """
        # 初始化各个验证器
        self.validators = {}
        
        if enable_sources is None:
            enable_sources = ['arxiv', 'crossref', 'openreview', 'scholar']
        
        if 'arxiv' in enable_sources:
            try:
                self.validators['arxiv'] = ArXivValidator()
                logger.info("ArXiv验证器已启用")
            except Exception as e:
                logger.warning(f"ArXiv验证器初始化失败: {e}")
        
        if 'crossref' in enable_sources:
            try:
                self.validators['crossref'] = CrossrefValidator()
                logger.info("Crossref验证器已启用")
            except Exception as e:
                logger.warning(f"Crossref验证器初始化失败: {e}")
        
        if 'openreview' in enable_sources:
            try:
                self.validators['openreview'] = OpenReviewValidator()
                logger.info("OpenReview验证器已启用")
            except Exception as e:
                logger.warning(f"OpenReview验证器初始化失败: {e}")
        
        if 'scholar' in enable_sources:
            try:
                self.validators['scholar'] = ScholarValidator()
                if self.validators['scholar'].available:
                    logger.info("Google Scholar验证器已启用")
                else:
                    logger.warning("Google Scholar验证器不可用（scholarly库未安装）")
                    del self.validators['scholar']
            except Exception as e:
                logger.warning(f"Google Scholar验证器初始化失败: {e}")
        
        logger.info(f"已启用 {len(self.validators)} 个验证源: {list(self.validators.keys())}")
    
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
    
    def _select_relevant_validators(self, entry: BibTeXEntry) -> List[str]:
        """
        根据条目特征选择相关的验证器
        
        Args:
            entry: BibTeXEntry对象
            
        Returns:
            相关验证器名称列表
        """
        relevant = []
        
        # 如果有ArXiv ID，优先使用ArXiv
        if entry.arxiv_id and 'arxiv' in self.validators:
            relevant.append('arxiv')
        
        # 如果有DOI，优先使用Crossref
        if entry.doi and 'crossref' in self.validators:
            relevant.append('crossref')
        
        # 如果是会议论文，使用OpenReview
        if entry.journal and any(
            conf in entry.journal.lower() 
            for conf in ['neurips', 'icml', 'iclr', 'aaai', 'ijcai', 'acl', 'emnlp', 'naacl', 'cvpr', 'iccv', 'eccv']
        ):
            if 'openreview' in self.validators:
                relevant.append('openreview')
        
        # 如果没有特定特征，使用所有可用的验证器
        if not relevant:
            relevant = list(self.validators.keys())
        
        return relevant
    
    def validate_entry(self, entry: BibTeXEntry) -> ValidationResult:
        """
        验证单条参考文献（多源交叉验证）
        
        Args:
            entry: BibTeXEntry对象
            
        Returns:
            ValidationResult对象
        """
        result = ValidationResult(entry)
        
        # 基础字段检查
        self._check_basic_fields(entry, result)
        
        # 选择相关的验证器
        relevant_validators = self._select_relevant_validators(entry)
        
        # 并行验证（实际是顺序执行，但可以优化为并行）
        for validator_name in relevant_validators:
            if validator_name not in self.validators:
                continue
            
            try:
                validator = self.validators[validator_name]
                validation_result = validator.validate_entry(entry)
                result.set_verification_source(validator_name, validation_result)
            except Exception as e:
                logger.error(f"{validator_name}验证器出错: {e}")
                result.set_verification_source(validator_name, {
                    'found': False,
                    'error': str(e)
                })
        
        # 计算最终置信度（基于多源交叉验证）
        result.calculate_confidence()
        
        # 如果多个源都未找到，标记为可疑
        if result.source_count == 0 and len(self.validators) > 1:
            result.add_issue("在多个数据源中均未找到匹配的论文")
        
        return result
    
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
