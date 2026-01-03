"""
Google Scholar 验证器
使用 scholarly 库访问 Google Scholar（注意：需要谨慎使用，遵守使用条款）
"""
import time
from typing import Dict, Optional, List
import logging
from .base_validator import BaseValidator

logger = logging.getLogger(__name__)

try:
    from scholarly import scholarly
    SCHOLARLY_AVAILABLE = True
except ImportError:
    SCHOLARLY_AVAILABLE = False
    logger.warning("scholarly库未安装，Google Scholar验证功能将不可用")


class ScholarValidator(BaseValidator):
    """Google Scholar 验证器（使用 scholarly 库）"""
    
    def __init__(self, delay: float = 2.0):
        """
        初始化Scholar验证器
        
        Args:
            delay: 请求之间的延迟（秒），避免被限制
        """
        super().__init__("scholar")
        self.delay = delay
        self.available = SCHOLARLY_AVAILABLE
        
        if not self.available:
            logger.warning("Google Scholar验证器不可用：scholarly库未安装")
    
    def search_by_title(self, title: str, year: Optional[str] = None) -> List[Dict]:
        """
        通过标题搜索论文
        
        Args:
            title: 论文标题
            year: 可选的年份过滤
            
        Returns:
            匹配的论文列表
        """
        if not self.available:
            return []
        
        try:
            if not title:
                return []
            
            # 使用scholarly搜索
            search_query = scholarly.search_pubs(title)
            results = []
            
            # 获取前几个结果
            for i, pub in enumerate(search_query):
                if i >= 5:  # 限制结果数量
                    break
                
                pub_dict = {
                    'title': pub.get('bib', {}).get('title', ''),
                    'authors': pub.get('bib', {}).get('author', []),
                    'year': pub.get('bib', {}).get('pub_year', ''),
                    'venue': pub.get('bib', {}).get('venue', ''),
                    'url': pub.get('pub_url', ''),
                    'scholar_id': pub.get('author_id', '')
                }
                
                # 年份过滤
                if year and pub_dict['year'] and str(pub_dict['year']) != year:
                    continue
                
                results.append(pub_dict)
                time.sleep(self.delay)
            
            return results
            
        except Exception as e:
            logger.error(f"Scholar标题搜索失败: {e}")
            return []
    
    def match_result(self, entry_title: str, entry_authors: List[str],
                    entry_year: Optional[str], result: Dict):
        """
        比较BibTeX条目和Scholar结果是否匹配
        
        Args:
            entry_title: BibTeX条目标题
            entry_authors: BibTeX条目作者列表
            entry_year: BibTeX条目年份
            result: Scholar搜索结果
            
        Returns:
            (是否匹配, 匹配详情字典)
        """
        match_details = {
            'title_match': False,
            'author_match': False,
            'year_match': False,
            'similarity_score': 0.0
        }
        
        # 标题匹配
        result_title = result.get('title', '')
        entry_title_norm = self.normalize_title(entry_title)
        result_title_norm = self.normalize_title(result_title)
        
        if entry_title_norm and result_title_norm:
            similarity = self.calculate_similarity(entry_title, result_title)
            if similarity >= 0.7:
                match_details['title_match'] = True
                match_details['similarity_score'] += similarity * 0.5
        
        # 作者匹配
        if entry_authors and result.get('authors'):
            entry_authors_norm = [self.normalize_author(a) for a in entry_authors]
            result_authors = [self.normalize_author(a) for a in result['authors']]
            
            common_authors = set(entry_authors_norm) & set(result_authors)
            if common_authors:
                match_details['author_match'] = True
                match_details['similarity_score'] += 0.3
        
        # 年份匹配
        if entry_year and result.get('year'):
            result_year = str(result['year'])
            if entry_year == result_year:
                match_details['year_match'] = True
                match_details['similarity_score'] += 0.2
        
        is_match = match_details['similarity_score'] >= 0.6
        
        return is_match, match_details
    
    def validate_entry(self, entry) -> Dict:
        """
        验证一条BibTeX条目
        
        Args:
            entry: BibTeXEntry对象
            
        Returns:
            验证结果字典
        """
        result = {
            'found': False,
            'matched_result': None,
            'match_details': {},
            'source_id': None,
            'source_url': None,
            'verification_method': None,
            'error': None
        }
        
        if not self.available:
            result['error'] = "scholarly库未安装"
            return result
        
        try:
            # 通过标题搜索
            if entry.title:
                search_results = self.search_by_title(entry.title, entry.year)
                
                best_match = None
                best_score = 0.0
                
                for search_result in search_results:
                    is_match, match_details = self.match_result(
                        entry.title,
                        entry.authors,
                        entry.year,
                        search_result
                    )
                    
                    if is_match and match_details['similarity_score'] > best_score:
                        best_match = search_result
                        best_score = match_details['similarity_score']
                        result['match_details'] = match_details
                
                if best_match:
                    result['found'] = True
                    result['matched_result'] = best_match
                    if best_match.get('url'):
                        result['source_url'] = best_match['url']
                    if best_match.get('scholar_id'):
                        result['source_id'] = best_match['scholar_id']
                    result['verification_method'] = 'title_search'
                    return result
            
            result['found'] = False
            
        except Exception as e:
            logger.error(f"Scholar验证条目失败: {e}")
            result['error'] = str(e)
        
        return result
