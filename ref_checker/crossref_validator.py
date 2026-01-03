"""
Crossref API 验证器
用于验证期刊和会议论文
"""
import requests
import time
from typing import Dict, Optional, List
import logging
from .base_validator import BaseValidator

logger = logging.getLogger(__name__)


class CrossrefValidator(BaseValidator):
    """Crossref API 验证器"""
    
    def __init__(self, delay: float = 0.5, user_agent: str = "LLM-Ref-Check/0.2.0"):
        """
        初始化Crossref验证器
        
        Args:
            delay: 请求之间的延迟（秒），避免API限制
            user_agent: User-Agent字符串
        """
        super().__init__("crossref")
        self.delay = delay
        self.base_url = "https://api.crossref.org/works"
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "application/json"
        }
    
    def search_by_doi(self, doi: str) -> Optional[Dict]:
        """
        通过DOI搜索论文
        
        Args:
            doi: DOI标识符
            
        Returns:
            论文信息字典，如果未找到则返回None
        """
        try:
            # 清理DOI
            doi = doi.strip()
            if doi.startswith('http'):
                # 提取DOI部分
                doi = doi.split('doi.org/')[-1] if 'doi.org/' in doi else doi
            
            url = f"{self.base_url}/{doi}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and 'message' in data:
                    return data['message']
            elif response.status_code == 404:
                logger.debug(f"DOI未找到: {doi}")
            else:
                logger.warning(f"Crossref API错误 {response.status_code}: {doi}")
            
            time.sleep(self.delay)
            return None
            
        except Exception as e:
            logger.error(f"Crossref DOI搜索失败 {doi}: {e}")
            return None
    
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
            
            params = {
                "query.title": title,
                "rows": 10,
                "sort": "relevance"
            }
            
            if year:
                params["filter"] = f"from-pub-date:{year}"
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and 'message' in data:
                    items = data['message'].get('items', [])
                    time.sleep(self.delay)
                    return items
            
            time.sleep(self.delay)
            return []
            
        except Exception as e:
            logger.error(f"Crossref标题搜索失败: {e}")
            return []
    
    def search_by_author_title(self, authors: List[str], title: str, 
                               year: Optional[str] = None) -> List[Dict]:
        """
        通过作者和标题搜索论文
        
        Args:
            authors: 作者列表
            title: 论文标题
            year: 可选的年份过滤
            
        Returns:
            匹配的论文列表
        """
        try:
            if not title or not authors:
                return []
            
            # 使用第一个作者和标题构建查询
            first_author = authors[0].split()[-1] if authors else ""
            
            params = {
                "query.title": title,
                "query.author": first_author,
                "rows": 10,
                "sort": "relevance"
            }
            
            if year:
                params["filter"] = f"from-pub-date:{year}"
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and 'message' in data:
                    items = data['message'].get('items', [])
                    time.sleep(self.delay)
                    return items
            
            time.sleep(self.delay)
            return []
            
        except Exception as e:
            logger.error(f"Crossref作者标题搜索失败: {e}")
            return []
    
    def match_result(self, entry_title: str, entry_authors: List[str],
                    entry_year: Optional[str], result: Dict):
        """
        比较BibTeX条目和Crossref结果是否匹配
        
        Args:
            entry_title: BibTeX条目标题
            entry_authors: BibTeX条目作者列表
            entry_year: BibTeX条目年份
            result: Crossref搜索结果
            
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
        result_title = result.get('title', [''])[0] if result.get('title') else ''
        entry_title_norm = self.normalize_title(entry_title)
        result_title_norm = self.normalize_title(result_title)
        
        if entry_title_norm and result_title_norm:
            similarity = self.calculate_similarity(entry_title, result_title)
            if similarity >= 0.7:
                match_details['title_match'] = True
                match_details['similarity_score'] += similarity * 0.5
        
        # 作者匹配
        if entry_authors and result.get('author'):
            entry_authors_norm = [self.normalize_author(a) for a in entry_authors]
            result_authors = []
            for author in result['author']:
                given = author.get('given', '')
                family = author.get('family', '')
                if family:
                    result_authors.append(self.normalize_author(family))
            
            common_authors = set(entry_authors_norm) & set(result_authors)
            if common_authors:
                match_details['author_match'] = True
                match_details['similarity_score'] += 0.3
        
        # 年份匹配
        if entry_year and result.get('published-print'):
            pub_dates = result['published-print'].get('date-parts', [])
            if pub_dates and len(pub_dates[0]) > 0:
                result_year = str(pub_dates[0][0])
                if entry_year == result_year:
                    match_details['year_match'] = True
                    match_details['similarity_score'] += 0.2
        
        # 如果相似度超过阈值，认为匹配
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
        
        try:
            # 方法1: 如果有DOI，直接查询
            if entry.doi:
                paper = self.search_by_doi(entry.doi)
                if paper:
                    result['found'] = True
                    result['matched_result'] = paper
                    result['source_id'] = entry.doi
                    result['source_url'] = f"https://doi.org/{entry.doi}"
                    result['verification_method'] = 'doi'
                    result['match_details'] = {
                        'title_match': True,
                        'author_match': True,
                        'year_match': True,
                        'similarity_score': 1.0
                    }
                    return result
            
            # 方法2: 通过标题和作者搜索
            if entry.title and entry.authors:
                search_results = self.search_by_author_title(
                    entry.authors,
                    entry.title,
                    entry.year
                )
                
                # 找到最佳匹配
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
                    # 获取DOI或URL
                    if best_match.get('DOI'):
                        result['source_id'] = best_match['DOI']
                        result['source_url'] = f"https://doi.org/{best_match['DOI']}"
                    elif best_match.get('URL'):
                        result['source_url'] = best_match['URL']
                    result['verification_method'] = 'title_author_search'
                    return result
            
            # 方法3: 仅通过标题搜索
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
                    if best_match.get('DOI'):
                        result['source_id'] = best_match['DOI']
                        result['source_url'] = f"https://doi.org/{best_match['DOI']}"
                    elif best_match.get('URL'):
                        result['source_url'] = best_match['URL']
                    result['verification_method'] = 'title_search'
                    return result
            
            # 未找到匹配
            result['found'] = False
            
        except Exception as e:
            logger.error(f"Crossref验证条目失败: {e}")
            result['error'] = str(e)
        
        return result
