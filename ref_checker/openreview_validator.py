"""
OpenReview API 验证器
用于验证会议论文（特别是机器学习会议）
"""
import requests
import time
from typing import Dict, Optional, List
import logging
from .base_validator import BaseValidator
from .improved_matcher import ImprovedMatcher

logger = logging.getLogger(__name__)


class OpenReviewValidator(BaseValidator):
    """OpenReview API 验证器"""
    
    def __init__(self, delay: float = 0.5):
        """
        初始化OpenReview验证器
        
        Args:
            delay: 请求之间的延迟（秒），避免API限制
        """
        super().__init__("openreview")
        self.delay = delay
        self.base_url = "https://api.openreview.net"
    
    def search_by_title(self, title: str, year: Optional[str] = None) -> List[Dict]:
        """
        通过标题搜索论文
        
        Args:
            title: 论文标题
            year: 可选的年份过滤
            
        Returns:
            匹配的论文列表
        """
        try:
            if not title:
                return []
            
            # OpenReview API 使用 GraphQL 或 REST
            # 这里使用简化的搜索方式
            url = f"{self.base_url}/notes"
            params = {
                "content": "all",
                "title": title,
                "limit": 10
            }
            
            if year:
                params["details"] = "replyCount,invitation,original"
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                notes = data.get('notes', [])
                time.sleep(self.delay)
                
                # 过滤年份（如果提供）
                if year:
                    filtered = []
                    for note in notes:
                        note_year = note.get('cdate', 0) // 10000000000  # 提取年份
                        if str(note_year) == year:
                            filtered.append(note)
                    return filtered
                
                return notes
            
            time.sleep(self.delay)
            return []
            
        except Exception as e:
            logger.error(f"OpenReview标题搜索失败: {e}")
            return []
    
    def search_by_venue(self, venue: str, year: Optional[str] = None) -> List[Dict]:
        """
        通过会议名称搜索论文
        
        Args:
            venue: 会议名称（如 NeurIPS, ICML, ICLR等）
            year: 可选的年份
            
        Returns:
            匹配的论文列表
        """
        try:
            url = f"{self.base_url}/notes"
            params = {
                "content": "all",
                "venue": venue,
                "limit": 50
            }
            
            if year:
                params["details"] = "replyCount,invitation,original"
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                notes = data.get('notes', [])
                time.sleep(self.delay)
                return notes
            
            time.sleep(self.delay)
            return []
            
        except Exception as e:
            logger.error(f"OpenReview会议搜索失败: {e}")
            return []
    
    def match_result(self, entry_title: str, entry_authors: List[str],
                    entry_year: Optional[str], result: Dict):
        """
        比较BibTeX条目和OpenReview结果是否匹配（使用改进的匹配算法）
        
        Args:
            entry_title: BibTeX条目标题
            entry_authors: BibTeX条目作者列表
            entry_year: BibTeX条目年份
            result: OpenReview搜索结果
            
        Returns:
            (是否匹配, 匹配详情字典)
        """
        # 提取结果信息
        result_title = result.get('content', {}).get('title', '')
        result_authors = result.get('content', {}).get('authors', [])
        result_year = None
        if result.get('cdate'):
            # OpenReview使用时间戳，提取年份
            result_year = str(result['cdate'] // 10000000000)
        
        # 使用改进的匹配算法
        is_match, match_details = ImprovedMatcher.calculate_match_score(
            entry_title, entry_authors, entry_year,
            result_title, result_authors, result_year
        )
        
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
        
        try:
            # OpenReview主要用于会议论文
            # 检查是否是会议论文（通过booktitle或journal字段判断）
            is_conference = bool(entry.journal and any(
                conf in entry.journal.lower() 
                for conf in ['neurips', 'icml', 'iclr', 'aaai', 'ijcai', 'acl', 'emnlp', 'naacl']
            ))
            
            if not is_conference:
                # 如果不是主要会议，跳过OpenReview验证
                result['found'] = False
                return result
            
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
                    note_id = best_match.get('id', '')
                    if note_id:
                        result['source_id'] = note_id
                        result['source_url'] = f"https://openreview.net/forum?id={note_id}"
                    result['verification_method'] = 'title_search'
                    return result
            
            result['found'] = False
            
        except Exception as e:
            logger.error(f"OpenReview验证条目失败: {e}")
            result['error'] = str(e)
        
        return result
