"""
改进的匹配算法
使用更智能的字符串相似度计算和匹配策略
"""
import re
from typing import Tuple, List, Optional
from difflib import SequenceMatcher


class ImprovedMatcher:
    """改进的匹配器，使用多种相似度算法"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        标准化文本用于比较
        
        Args:
            text: 原始文本
            
        Returns:
            标准化后的文本
        """
        if not text:
            return ""
        
        # 转换为小写
        text = text.lower()
        
        # 移除常见的标点符号和特殊字符
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 移除多余空格
        text = ' '.join(text.split())
        
        # 移除常见的停用词（可选，但可能影响准确性）
        # 暂时保留所有词
        
        return text.strip()
    
    @staticmethod
    def sequence_similarity(text1: str, text2: str) -> float:
        """
        使用SequenceMatcher计算相似度（0.0-1.0）
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数
        """
        if not text1 or not text2:
            return 0.0
        
        return SequenceMatcher(None, text1, text2).ratio()
    
    @staticmethod
    def word_overlap_similarity(text1: str, text2: str) -> float:
        """
        计算词汇重叠相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数
        """
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard相似度
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def substring_similarity(text1: str, text2: str) -> float:
        """
        检查子串包含关系
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数
        """
        if not text1 or not text2:
            return 0.0
        
        norm1 = ImprovedMatcher.normalize_text(text1)
        norm2 = ImprovedMatcher.normalize_text(text2)
        
        if norm1 == norm2:
            return 1.0
        
        # 检查包含关系
        if norm1 in norm2 or norm2 in norm1:
            # 计算包含比例
            shorter = min(len(norm1), len(norm2))
            longer = max(len(norm1), len(norm2))
            return shorter / longer if longer > 0 else 0.0
        
        return 0.0
    
    @staticmethod
    def calculate_title_similarity(title1: str, title2: str) -> float:
        """
        计算标题相似度（综合多种方法，改进版）
        
        Args:
            title1: 标题1
            title2: 标题2
            
        Returns:
            综合相似度分数 (0.0-1.0)
        """
        if not title1 or not title2:
            return 0.0
        
        norm1 = ImprovedMatcher.normalize_text(title1)
        norm2 = ImprovedMatcher.normalize_text(title2)
        
        # 完全匹配
        if norm1 == norm2:
            return 1.0
        
        # 计算多种相似度
        seq_sim = ImprovedMatcher.sequence_similarity(norm1, norm2)
        word_sim = ImprovedMatcher.word_overlap_similarity(norm1, norm2)
        substr_sim = ImprovedMatcher.substring_similarity(norm1, norm2)
        
        # 改进：检查重要词汇匹配
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        # 移除常见停用词
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from'}
        words1 = {w for w in words1 if w not in stopwords and len(w) > 2}
        words2 = {w for w in words2 if w not in stopwords and len(w) > 2}
        
        if words1 and words2:
            important_overlap = len(words1 & words2) / max(len(words1), len(words2))
        else:
            important_overlap = 0.0
        
        # 加权平均（更重视重要词汇重叠和词汇重叠）
        similarity = (
            seq_sim * 0.25 +
            word_sim * 0.35 +
            substr_sim * 0.15 +
            important_overlap * 0.25
        )
        
        # 如果重要词汇完全匹配，提高相似度
        if words1 and words2 and (words1.issubset(words2) or words2.issubset(words1)):
            similarity = max(similarity, 0.75)
        
        return similarity
    
    @staticmethod
    def extract_author_family_name(author: str) -> str:
        """
        提取作者的姓氏
        
        Args:
            author: 作者名称（可能是 "Last, First" 或 "First Last" 格式）
            
        Returns:
            姓氏
        """
        if not author:
            return ""
        
        author = author.strip()
        
        # 处理 "Last, First" 格式
        if ',' in author:
            parts = [p.strip() for p in author.split(',')]
            return parts[0].lower() if parts else ""
        
        # 处理 "First Last" 格式
        parts = author.split()
        if parts:
            # 通常最后一个词是姓氏
            return parts[-1].lower()
        
        return author.lower()
    
    @staticmethod
    def match_authors(entry_authors: List[str], result_authors: List[str]) -> Tuple[bool, float]:
        """
        匹配作者列表
        
        Args:
            entry_authors: BibTeX条目作者列表
            result_authors: 搜索结果作者列表
            
        Returns:
            (是否匹配, 匹配分数)
        """
        if not entry_authors or not result_authors:
            return False, 0.0
        
        # 提取所有姓氏
        entry_families = {ImprovedMatcher.extract_author_family_name(a) for a in entry_authors}
        result_families = {ImprovedMatcher.extract_author_family_name(a) for a in result_authors}
        
        # 移除空字符串
        entry_families = {f for f in entry_families if f}
        result_families = {f for f in result_families if f}
        
        if not entry_families or not result_families:
            return False, 0.0
        
        # 计算共同作者
        common = entry_families & result_families
        
        if not common:
            return False, 0.0
        
        # 计算匹配分数（共同作者比例）
        match_score = len(common) / max(len(entry_families), len(result_families))
        
        # 至少有一个共同作者就认为匹配
        return True, match_score
    
    @staticmethod
    def match_year(entry_year: Optional[str], result_year: Optional[str], tolerance: int = 1) -> bool:
        """
        匹配年份（允许一定容差）
        
        Args:
            entry_year: BibTeX条目年份
            result_year: 结果年份
            tolerance: 允许的年份差异
            
        Returns:
            是否匹配
        """
        if not entry_year or not result_year:
            return False
        
        try:
            entry_y = int(entry_year)
            result_y = int(result_year)
            return abs(entry_y - result_y) <= tolerance
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def calculate_match_score(entry_title: str, entry_authors: List[str], entry_year: Optional[str],
                             result_title: str, result_authors: List[str], result_year: Optional[str]) -> Tuple[bool, dict]:
        """
        计算综合匹配分数
        
        Args:
            entry_title: BibTeX条目标题
            entry_authors: BibTeX条目作者列表
            entry_year: BibTeX条目年份
            result_title: 结果标题
            result_authors: 结果作者列表
            result_year: 结果年份
            
        Returns:
            (是否匹配, 匹配详情字典)
        """
        match_details = {
            'title_match': False,
            'author_match': False,
            'year_match': False,
            'title_similarity': 0.0,
            'author_similarity': 0.0,
            'similarity_score': 0.0
        }
        
        # 标题相似度
        title_sim = ImprovedMatcher.calculate_title_similarity(entry_title, result_title)
        match_details['title_similarity'] = title_sim
        
        # 降低标题匹配阈值（从0.7降到0.5）
        if title_sim >= 0.5:
            match_details['title_match'] = True
            # 标题匹配权重提高
            match_details['similarity_score'] += title_sim * 0.6
        
        # 作者匹配
        author_match, author_sim = ImprovedMatcher.match_authors(entry_authors, result_authors)
        match_details['author_match'] = author_match
        match_details['author_similarity'] = author_sim
        
        if author_match:
            match_details['similarity_score'] += author_sim * 0.3
        
        # 年份匹配（允许1年容差）
        year_match = ImprovedMatcher.match_year(entry_year, result_year, tolerance=1)
        match_details['year_match'] = year_match
        
        if year_match:
            match_details['similarity_score'] += 0.1
        elif entry_year and result_year:
            # 年份不匹配但不严重（差异在2年内）
            try:
                entry_y = int(entry_year)
                result_y = int(result_year)
                if abs(entry_y - result_y) <= 2:
                    match_details['similarity_score'] += 0.05  # 小幅扣分
            except (ValueError, TypeError):
                pass
        
        # 降低匹配阈值（从0.6降到0.35）
        # 如果标题相似度很高，即使其他条件稍弱也认为匹配
        is_match = (
            match_details['similarity_score'] >= 0.35 or
            (title_sim >= 0.65 and author_match) or  # 降低标题阈值
            (title_sim >= 0.75) or  # 标题高度相似就认为匹配
            (title_sim >= 0.5 and author_match and year_match)  # 标题中等相似+作者+年份
        )
        
        return is_match, match_details
