"""
ArXiv API验证器
用于验证CS领域的论文是否真实存在于ArXiv
"""
import arxiv
from typing import List, Dict, Optional, Tuple
import logging
import time
import re

logger = logging.getLogger(__name__)


class ArXivValidator:
    """ArXiv论文验证器"""
    
    def __init__(self, max_results: int = 10, delay: float = 0.5):
        """
        初始化ArXiv验证器
        
        Args:
            max_results: 每次搜索返回的最大结果数
            delay: 请求之间的延迟（秒），避免API限制
        """
        self.max_results = max_results
        self.delay = delay
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=delay,
            num_retries=3
        )
    
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
        # 转换为小写，移除标点符号和多余空格
        normalized = title.lower()
        # 移除常见的标点符号
        normalized = re.sub(r'[^\w\s]', '', normalized)
        # 移除多余空格
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
        # 移除常见的前缀和后缀
        author = author.strip()
        # 转换为小写用于比较
        return author.lower()
    
    def search_by_arxiv_id(self, arxiv_id: str) -> Optional[arxiv.Result]:
        """
        通过ArXiv ID搜索论文
        
        Args:
            arxiv_id: ArXiv ID (例如: 1706.03762)
            
        Returns:
            ArXiv结果对象，如果未找到则返回None
        """
        try:
            # 清理ArXiv ID
            arxiv_id = arxiv_id.strip()
            # 移除可能的版本号
            arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
            
            search = arxiv.Search(
                id_list=[arxiv_id],
                max_results=1
            )
            
            results = list(self.client.results(search))
            if results:
                return results[0]
            return None
            
        except Exception as e:
            logger.warning(f"通过ArXiv ID搜索失败 {arxiv_id}: {e}")
            return None
    
    def search_by_title(self, title: str, year: Optional[str] = None) -> List[arxiv.Result]:
        """
        通过标题搜索论文
        
        Args:
            title: 论文标题
            year: 可选的年份过滤
            
        Returns:
            匹配的ArXiv结果列表
        """
        try:
            if not title:
                return []
            
            # 构建搜索查询
            # 使用标题的主要关键词
            query = f'ti:"{title}"'
            if year:
                query += f' AND submittedDate:[{year}01010000 TO {year}12312359]'
            
            search = arxiv.Search(
                query=query,
                max_results=self.max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            results = list(self.client.results(search))
            time.sleep(self.delay)  # 避免API限制
            
            return results
            
        except Exception as e:
            logger.warning(f"通过标题搜索失败: {e}")
            return []
    
    def search_by_author_title(self, authors: List[str], title: str, 
                               year: Optional[str] = None) -> List[arxiv.Result]:
        """
        通过作者和标题搜索论文
        
        Args:
            authors: 作者列表
            title: 论文标题
            year: 可选的年份过滤
            
        Returns:
            匹配的ArXiv结果列表
        """
        try:
            if not title or not authors:
                return []
            
            # 使用第一个作者和标题构建查询
            first_author = authors[0].split()[-1] if authors else ""
            query = f'au:"{first_author}" AND ti:"{title}"'
            if year:
                query += f' AND submittedDate:[{year}01010000 TO {year}12312359]'
            
            search = arxiv.Search(
                query=query,
                max_results=self.max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            results = list(self.client.results(search))
            time.sleep(self.delay)
            
            return results
            
        except Exception as e:
            logger.warning(f"通过作者和标题搜索失败: {e}")
            return []
    
    def match_result(self, entry_title: str, entry_authors: List[str], 
                    entry_year: Optional[str], result: arxiv.Result) -> Tuple[bool, Dict]:
        """
        比较BibTeX条目和ArXiv结果是否匹配
        
        Args:
            entry_title: BibTeX条目标题
            entry_authors: BibTeX条目作者列表
            entry_year: BibTeX条目年份
            result: ArXiv搜索结果
            
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
        entry_title_norm = self.normalize_title(entry_title)
        result_title_norm = self.normalize_title(result.title)
        
        if entry_title_norm and result_title_norm:
            # 简单的相似度计算（可以改进为更复杂的算法）
            if entry_title_norm == result_title_norm:
                match_details['title_match'] = True
                match_details['similarity_score'] += 0.5
            elif entry_title_norm in result_title_norm or result_title_norm in entry_title_norm:
                match_details['title_match'] = True
                match_details['similarity_score'] += 0.3
        
        # 作者匹配
        if entry_authors and result.authors:
            entry_authors_norm = [self.normalize_author(a) for a in entry_authors]
            result_authors_norm = [self.normalize_author(str(a)) for a in result.authors]
            
            # 检查是否有共同作者
            common_authors = set(entry_authors_norm) & set(result_authors_norm)
            if common_authors:
                match_details['author_match'] = True
                match_details['similarity_score'] += 0.3
        
        # 年份匹配
        if entry_year and result.published:
            result_year = str(result.published.year)
            if entry_year == result_year:
                match_details['year_match'] = True
                match_details['similarity_score'] += 0.2
        
        # 如果相似度超过阈值，认为匹配
        is_match = match_details['similarity_score'] >= 0.5
        
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
            'arxiv_id': None,
            'arxiv_url': None,
            'verification_method': None,
            'error': None
        }
        
        try:
            # 方法1: 如果有ArXiv ID，直接查询
            if entry.arxiv_id:
                arxiv_result = self.search_by_arxiv_id(entry.arxiv_id)
                if arxiv_result:
                    result['found'] = True
                    result['matched_result'] = arxiv_result
                    # 提取ArXiv ID (entry_id格式: http://arxiv.org/abs/1706.03762v7 -> 1706.03762)
                    entry_id = arxiv_result.entry_id
                    # 从URL中提取ID
                    if 'arxiv.org/abs/' in entry_id:
                        arxiv_id_clean = entry_id.split('arxiv.org/abs/')[-1].split('v')[0]
                    elif 'arXiv:' in entry_id:
                        arxiv_id_clean = entry_id.replace('arXiv:', '').split('v')[0]
                    else:
                        arxiv_id_clean = entry_id.split('v')[0]
                    result['arxiv_id'] = arxiv_id_clean
                    result['arxiv_url'] = f"https://arxiv.org/abs/{arxiv_id_clean}"
                    result['verification_method'] = 'arxiv_id'
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
                    # 提取ArXiv ID
                    entry_id = best_match.entry_id
                    if 'arxiv.org/abs/' in entry_id:
                        arxiv_id_clean = entry_id.split('arxiv.org/abs/')[-1].split('v')[0]
                    elif 'arXiv:' in entry_id:
                        arxiv_id_clean = entry_id.replace('arXiv:', '').split('v')[0]
                    else:
                        arxiv_id_clean = entry_id.split('v')[0]
                    result['arxiv_id'] = arxiv_id_clean
                    result['arxiv_url'] = f"https://arxiv.org/abs/{arxiv_id_clean}"
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
                    # 提取ArXiv ID
                    entry_id = best_match.entry_id
                    if 'arxiv.org/abs/' in entry_id:
                        arxiv_id_clean = entry_id.split('arxiv.org/abs/')[-1].split('v')[0]
                    elif 'arXiv:' in entry_id:
                        arxiv_id_clean = entry_id.replace('arXiv:', '').split('v')[0]
                    else:
                        arxiv_id_clean = entry_id.split('v')[0]
                    result['arxiv_id'] = arxiv_id_clean
                    result['arxiv_url'] = f"https://arxiv.org/abs/{arxiv_id_clean}"
                    result['verification_method'] = 'title_search'
                    return result
            
            # 未找到匹配
            result['found'] = False
            
        except Exception as e:
            logger.error(f"验证条目失败: {e}")
            result['error'] = str(e)
        
        return result
