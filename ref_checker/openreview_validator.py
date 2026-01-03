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
from .detailed_validator import DetailedValidator

logger = logging.getLogger(__name__)


class OpenReviewValidator(BaseValidator):
    """OpenReview API 验证器"""
    
    def __init__(self, delay: float = 1.0):
        """
        初始化OpenReview验证器
        
        Args:
            delay: 请求之间的延迟（秒），避免API限制（默认1秒）
        """
        super().__init__("openreview")
        self.delay = delay
        self.base_url = "https://api.openreview.net"
        
        # 会议invitation映射
        self.conference_invitations = {
            'ijcai': {
                '2019': 'IJCAI.org/2019/Conference/-/Blind_Submission',
                '2020': 'IJCAI.org/2020/Conference/-/Blind_Submission',
                '2021': 'IJCAI.org/2021/Conference/-/Blind_Submission',
                '2022': 'IJCAI.org/2022/Conference/-/Blind_Submission',
                '2023': 'IJCAI.org/2023/Conference/-/Blind_Submission',
            },
            'neurips': {
                '2019': 'NeurIPS.cc/2019/Conference/-/Blind_Submission',
                '2020': 'NeurIPS.cc/2020/Conference/-/Blind_Submission',
                '2021': 'NeurIPS.cc/2021/Conference/-/Blind_Submission',
            },
            'icml': {
                '2019': 'ICML.cc/2019/Conference/-/Blind_Submission',
                '2020': 'ICML.cc/2020/Conference/-/Blind_Submission',
            },
            'iclr': {
                '2019': 'ICLR.cc/2019/Conference/-/Blind_Submission',
                '2020': 'ICLR.cc/2020/Conference/-/Blind_Submission',
            },
        }
    
    def search_by_title(self, title: str, year: Optional[str] = None) -> List[Dict]:
        """
        通过标题搜索论文（改进：使用正确的API参数）
        
        Args:
            title: 论文标题
            year: 可选的年份过滤
            
        Returns:
            匹配的论文列表
        """
        try:
            if not title:
                return []
            
            # OpenReview API 正确的参数格式
            url = f"{self.base_url}/notes"
            params = {
                "content.title": title,  # 正确的参数名
                "details": "replyCount,invitation,original",
                "limit": 20  # 增加结果数量
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                notes = data.get('notes', [])
                time.sleep(self.delay)
                
                # 过滤年份（如果提供）
                if year:
                    filtered = []
                    for note in notes:
                        # 从cdate提取年份（时间戳格式）
                        cdate = note.get('cdate', 0)
                        if cdate:
                            note_year = str(cdate // 10000000000)
                            if note_year == year:
                                filtered.append(note)
                        # 也可以从invitation中提取年份
                        invitation = note.get('invitation', '')
                        if year in invitation:
                            filtered.append(note)
                    # 去重
                    seen_ids = set()
                    unique_notes = []
                    for note in filtered:
                        note_id = note.get('id')
                        if note_id and note_id not in seen_ids:
                            seen_ids.add(note_id)
                            unique_notes.append(note)
                    return unique_notes
                
                return notes
            
            elif response.status_code == 429:
                logger.warning("OpenReview API请求频率限制，等待后重试...")
                time.sleep(3)  # 增加等待时间
                # 不重试，直接返回空，避免无限循环
                return []
            
            time.sleep(self.delay)
            return []
            
        except Exception as e:
            logger.error(f"OpenReview标题搜索失败: {e}")
            return []
    
    def search_by_invitation(self, conference: str, year: str, title: Optional[str] = None) -> List[Dict]:
        """
        通过会议invitation搜索论文（更精确）
        
        Args:
            conference: 会议名称（小写，如 'ijcai', 'neurips'）
            year: 年份
            title: 可选的标题（用于进一步过滤）
            
        Returns:
            匹配的论文列表
        """
        try:
            # 获取invitation
            conf_map = self.conference_invitations.get(conference.lower(), {})
            invitation = conf_map.get(year)
            
            if not invitation:
                return []
            
            url = f"{self.base_url}/notes"
            params = {
                "invitation": invitation,
                "details": "replyCount,invitation,original",
                "limit": 100
            }
            
            # 如果提供了标题，添加标题搜索
            if title:
                params["content.title"] = title
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                notes = data.get('notes', [])
                time.sleep(self.delay)
                return notes
            elif response.status_code == 429:
                logger.warning("OpenReview API请求频率限制")
                time.sleep(3)
                return []
            
            time.sleep(self.delay)
            return []
            
        except Exception as e:
            logger.error(f"OpenReview invitation搜索失败: {e}")
            return []
    
    def match_result(self, entry_title: str, entry_authors: List[str],
                    entry_year: Optional[str], result: Dict):
        """
        比较BibTeX条目和OpenReview结果是否匹配（使用详细验证）
        
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
        
        # 使用详细验证器进行字段级验证
        entry_dict = {
            'title': entry_title,
            'authors': entry_authors,
            'year': entry_year,
            'doi': None
        }
        
        detailed_result = DetailedValidator.comprehensive_validate(
            entry_dict,
            result,
            'openreview'
        )
        
        # 转换为原有格式
        match_details = {
            'title_match': detailed_result['field_validations']['title'].get('match', False),
            'author_match': detailed_result['field_validations']['authors'].get('match', False),
            'year_match': detailed_result['field_validations']['year'].get('match', False),
            'similarity_score': detailed_result['confidence'],
            'title_similarity': detailed_result['field_validations']['title'].get('similarity', 0.0),
            'author_similarity': detailed_result['field_validations']['authors'].get('match_ratio', 0.0),
            'is_hallucination': detailed_result.get('is_hallucination', False),
            'issues': detailed_result.get('issues', []),
            'warnings': detailed_result.get('warnings', []),
            'detailed_validation': detailed_result
        }
        
        is_match = detailed_result['overall_match']
        
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
            journal_lower = (entry.journal or '').lower()
            is_conference = any(
                conf in journal_lower 
                for conf in ['neurips', 'icml', 'iclr', 'aaai', 'ijcai', 'acl', 'emnlp', 'naacl', 'cvpr', 'iccv', 'eccv']
            )
            
            if not is_conference:
                # 如果不是主要会议，跳过OpenReview验证
                result['found'] = False
                return result
            
            # 识别会议名称
            conference_name = None
            for conf in ['ijcai', 'neurips', 'icml', 'iclr', 'aaai']:
                if conf in journal_lower:
                    conference_name = conf
                    break
            
            # 方法1: 如果知道会议和年份，通过invitation搜索（更精确）
            if conference_name and entry.year:
                search_results = self.search_by_invitation(
                    conference_name,
                    entry.year,
                    entry.title
                )
                
                if search_results:
                    best_match = None
                    best_score = -1.0
                    
                    for search_result in search_results:
                        is_match, match_details = self.match_result(
                            entry.title,
                            entry.authors,
                            entry.year,
                            search_result
                        )
                        
                        score = match_details.get('similarity_score', 0.0)
                        if score > best_score:
                            best_match = search_result
                            best_score = score
                            result['match_details'] = match_details
                        
                        if is_match:
                            result['found'] = True
                            result['matched_result'] = best_match
                            note_id = best_match.get('id', '')
                            if note_id:
                                result['source_id'] = note_id
                                result['source_url'] = f"https://openreview.net/forum?id={note_id}"
                            result['verification_method'] = 'invitation_search'
                            return result
                    
                    # 如果没有完全匹配，但最高分足够高，也认为找到
                    if best_match and best_score >= 0.35:
                        result['found'] = True
                        result['matched_result'] = best_match
                        note_id = best_match.get('id', '')
                        if note_id:
                            result['source_id'] = note_id
                            result['source_url'] = f"https://openreview.net/forum?id={note_id}"
                        result['verification_method'] = 'invitation_search'
                        return result
            
            # 方法2: 通过标题搜索（备用方法）
            if entry.title:
                search_results = self.search_by_title(entry.title, entry.year)
                
                best_match = None
                best_score = -1.0
                
                for search_result in search_results:
                    is_match, match_details = self.match_result(
                        entry.title,
                        entry.authors,
                        entry.year,
                        search_result
                    )
                    
                    score = match_details.get('similarity_score', 0.0)
                    if score > best_score:
                        best_match = search_result
                        best_score = score
                        result['match_details'] = match_details
                    
                    if is_match:
                        result['found'] = True
                        result['matched_result'] = best_match
                        note_id = best_match.get('id', '')
                        if note_id:
                            result['source_id'] = note_id
                            result['source_url'] = f"https://openreview.net/forum?id={note_id}"
                        result['verification_method'] = 'title_search'
                        return result
                
                if best_match and best_score >= 0.35:
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
