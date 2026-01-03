"""
验证器基类
定义统一的验证接口，便于扩展多个数据源
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class BaseValidator(ABC):
    """验证器基类"""
    
    def __init__(self, name: str):
        """
        初始化验证器
        
        Args:
            name: 验证器名称
        """
        self.name = name
    
    @abstractmethod
    def validate_entry(self, entry) -> Dict:
        """
        验证一条参考文献条目
        
        Args:
            entry: BibTeXEntry对象
            
        Returns:
            验证结果字典，包含：
            - found: bool - 是否找到匹配
            - matched_result: 匹配结果对象
            - match_details: dict - 匹配详情
            - source_id: str - 数据源ID（如DOI、ArXiv ID等）
            - source_url: str - 数据源URL
            - verification_method: str - 验证方法
            - error: str - 错误信息（如果有）
        """
        pass
    
    def normalize_title(self, title: str) -> str:
        """
        标准化标题用于比较
        
        Args:
            title: 原始标题
            
        Returns:
            标准化后的标题
        """
        if not title:
            return ""
        import re
        # 转换为小写，移除标点符号和多余空格
        normalized = title.lower()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = ' '.join(normalized.split())
        return normalized
    
    def normalize_author(self, author: str) -> str:
        """
        标准化作者名称用于比较
        
        Args:
            author: 原始作者名称
            
        Returns:
            标准化后的作者名称
        """
        if not author:
            return ""
        return author.strip().lower()
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度（简单版本）
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数 (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        norm1 = self.normalize_title(text1)
        norm2 = self.normalize_title(text2)
        
        if norm1 == norm2:
            return 1.0
        
        # 简单的包含关系检查
        if norm1 in norm2 or norm2 in norm1:
            return 0.8
        
        # 计算共同词汇比例
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0.0
        
        common = words1 & words2
        total = words1 | words2
        
        return len(common) / len(total) if total else 0.0
