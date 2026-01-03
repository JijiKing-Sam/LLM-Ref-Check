"""
详细验证器 - 字段级验证
检测部分信息正确但其他信息错误的幻觉引用
参考GPTZero的Hallucination Check方法
"""
from typing import Dict, List, Optional, Tuple
from .improved_matcher import ImprovedMatcher
import logging

logger = logging.getLogger(__name__)


class DetailedValidator:
    """
    详细验证器
    不仅检查是否找到匹配，还验证每个字段的准确性
    """
    
    @staticmethod
    def extract_author_names(author_str: str) -> Tuple[str, str]:
        """
        提取作者的姓氏和名字
        
        Args:
            author_str: 作者字符串，可能是 "Last, First" 或 "First Last" 格式
            
        Returns:
            (family_name, given_name)
        """
        if not author_str:
            return "", ""
        
        author_str = author_str.strip()
        
        # 处理 "Last, First" 格式
        if ',' in author_str:
            parts = [p.strip() for p in author_str.split(',', 1)]
            if len(parts) >= 2:
                return parts[0].lower(), parts[1].lower()
            elif len(parts) == 1:
                return parts[0].lower(), ""
        
        # 处理 "First Last" 格式
        parts = author_str.split()
        if len(parts) >= 2:
            # 通常最后一个词是姓氏
            return parts[-1].lower(), ' '.join(parts[:-1]).lower()
        elif len(parts) == 1:
            return parts[0].lower(), ""
        
        return author_str.lower(), ""
    
    @staticmethod
    def normalize_author_list(authors: List[str]) -> List[Dict[str, str]]:
        """
        标准化作者列表，提取每个作者的姓氏和名字
        
        Args:
            authors: 作者字符串列表
            
        Returns:
            包含 {family, given} 的字典列表
        """
        normalized = []
        for author in authors:
            family, given = DetailedValidator.extract_author_names(author)
            normalized.append({
                'family': family,
                'given': given,
                'original': author
            })
        return normalized
    
    @staticmethod
    def validate_title(entry_title: str, result_title: str) -> Dict:
        """
        验证标题
        
        Returns:
            {
                'match': bool,
                'similarity': float,
                'is_exact': bool,
                'issue': str (如果有问题)
            }
        """
        if not entry_title or not result_title:
            return {
                'match': False,
                'similarity': 0.0,
                'is_exact': False,
                'issue': '标题缺失'
            }
        
        similarity = ImprovedMatcher.calculate_title_similarity(entry_title, result_title)
        is_exact = ImprovedMatcher.normalize_text(entry_title) == ImprovedMatcher.normalize_text(result_title)
        
        result = {
            'match': similarity >= 0.5,  # 降低阈值以检测部分匹配
            'similarity': similarity,
            'is_exact': is_exact
        }
        
        if similarity < 0.5:
            result['issue'] = f'标题相似度低 ({similarity:.2%})'
        elif not is_exact and similarity < 0.8:
            result['warning'] = f'标题不完全匹配 (相似度: {similarity:.2%})'
        
        return result
    
    @staticmethod
    def validate_authors(entry_authors: List[str], result_authors: List[str]) -> Dict:
        """
        验证作者列表（字段级验证）
        
        Returns:
            {
                'match': bool,
                'exact_match_count': int,
                'partial_match_count': int,
                'total_entry': int,
                'total_result': int,
                'matched_authors': List[Dict],
                'missing_authors': List[str],
                'extra_authors': List[str],
                'issues': List[str]
            }
        """
        if not entry_authors:
            return {
                'match': False,
                'exact_match_count': 0,
                'partial_match_count': 0,
                'total_entry': 0,
                'total_result': len(result_authors) if result_authors else 0,
                'matched_authors': [],
                'missing_authors': [],
                'extra_authors': result_authors.copy() if result_authors else [],
                'issues': ['BibTeX条目缺少作者信息']
            }
        
        if not result_authors:
            return {
                'match': False,
                'exact_match_count': 0,
                'partial_match_count': 0,
                'total_entry': len(entry_authors),
                'total_result': 0,
                'matched_authors': [],
                'missing_authors': entry_authors.copy(),
                'extra_authors': [],
                'issues': ['搜索结果缺少作者信息']
            }
        
        # 标准化作者列表
        entry_normalized = DetailedValidator.normalize_author_list(entry_authors)
        result_normalized = DetailedValidator.normalize_author_list(result_authors)
        
        # 匹配作者
        matched_authors = []
        missing_authors = []
        issues = []
        
        # 检查每个BibTeX作者是否在结果中找到
        for entry_author in entry_normalized:
            entry_family = entry_author['family']
            entry_given = entry_author['given']
            
            found = False
            match_type = None
            
            for result_author in result_normalized:
                result_family = result_author['family']
                result_given = result_author['given']
                
                # 完全匹配（姓氏和名字都匹配）
                if entry_family == result_family and entry_given == result_given:
                    matched_authors.append({
                        'entry': entry_author['original'],
                        'result': result_author['original'],
                        'match_type': 'exact'
                    })
                    found = True
                    match_type = 'exact'
                    break
                # 部分匹配（仅姓氏匹配）
                elif entry_family == result_family:
                    matched_authors.append({
                        'entry': entry_author['original'],
                        'result': result_author['original'],
                        'match_type': 'partial'
                    })
                    found = True
                    match_type = 'partial'
                    break
            
            if not found:
                missing_authors.append(entry_author['original'])
        
        # 检查结果中是否有BibTeX中没有的作者
        entry_families = {a['family'] for a in entry_normalized}
        extra_authors = [
            r['original'] for r in result_normalized 
            if r['family'] not in entry_families
        ]
        
        # 统计
        exact_count = sum(1 for m in matched_authors if m['match_type'] == 'exact')
        partial_count = sum(1 for m in matched_authors if m['match_type'] == 'partial')
        
        # 判断是否有问题
        total_entry = len(entry_authors)
        match_ratio = len(matched_authors) / total_entry if total_entry > 0 else 0.0
        
        # 如果匹配的作者少于50%，认为有问题
        if match_ratio < 0.5:
            issues.append(f'只有 {len(matched_authors)}/{total_entry} 个作者匹配 ({match_ratio:.1%})')
        
        # 如果有很多额外作者，可能是幻觉
        if len(extra_authors) > len(matched_authors) * 0.5:
            issues.append(f'搜索结果中有 {len(extra_authors)} 个额外作者')
        
        # 如果部分匹配太多，可能是姓氏相同但名字不同
        if partial_count > exact_count:
            issues.append(f'有 {partial_count} 个作者仅姓氏匹配，名字不匹配')
        
        return {
            'match': match_ratio >= 0.5,  # 至少50%作者匹配
            'exact_match_count': exact_count,
            'partial_match_count': partial_count,
            'total_entry': total_entry,
            'total_result': len(result_authors),
            'matched_authors': matched_authors,
            'missing_authors': missing_authors,
            'extra_authors': extra_authors,
            'match_ratio': match_ratio,
            'issues': issues
        }
    
    @staticmethod
    def validate_year(entry_year: Optional[str], result_year: Optional[str]) -> Dict:
        """
        验证年份
        
        Returns:
            {
                'match': bool,
                'entry_year': str,
                'result_year': str,
                'difference': int,
                'issue': str (如果有问题)
            }
        """
        if not entry_year:
            return {
                'match': False,
                'entry_year': None,
                'result_year': result_year,
                'difference': None,
                'issue': 'BibTeX条目缺少年份'
            }
        
        if not result_year:
            return {
                'match': False,
                'entry_year': entry_year,
                'result_year': None,
                'difference': None,
                'issue': '搜索结果缺少年份'
            }
        
        try:
            entry_y = int(entry_year)
            result_y = int(result_year)
            difference = abs(entry_y - result_y)
            
            result = {
                'match': difference <= 1,  # 允许1年容差
                'entry_year': entry_year,
                'result_year': result_year,
                'difference': difference
            }
            
            if difference > 1:
                result['issue'] = f'年份差异 {difference} 年'
            elif difference == 1:
                result['warning'] = '年份有1年差异（可能是发表时间差异）'
            
            return result
            
        except (ValueError, TypeError):
            return {
                'match': False,
                'entry_year': entry_year,
                'result_year': result_year,
                'difference': None,
                'issue': '年份格式无效'
            }
    
    @staticmethod
    def validate_doi(entry_doi: Optional[str], result_doi: Optional[str]) -> Dict:
        """
        验证DOI
        
        Returns:
            {
                'match': bool,
                'entry_doi': str,
                'result_doi': str,
                'issue': str (如果有问题)
            }
        """
        if not entry_doi and not result_doi:
            return {
                'match': True,  # 都没有DOI，不算问题
                'entry_doi': None,
                'result_doi': None
            }
        
        if entry_doi and not result_doi:
            return {
                'match': False,
                'entry_doi': entry_doi,
                'result_doi': None,
                'warning': 'BibTeX有DOI但搜索结果没有'
            }
        
        if not entry_doi and result_doi:
            return {
                'match': True,  # BibTeX没有但结果有，不算问题
                'entry_doi': None,
                'result_doi': result_doi,
                'info': '搜索结果提供了DOI'
            }
        
        # 标准化DOI（移除URL前缀）
        entry_doi_clean = entry_doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '').strip()
        result_doi_clean = result_doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '').strip()
        
        match = entry_doi_clean.lower() == result_doi_clean.lower()
        
        result = {
            'match': match,
            'entry_doi': entry_doi,
            'result_doi': result_doi
        }
        
        if not match:
            result['issue'] = f'DOI不匹配: {entry_doi_clean} vs {result_doi_clean}'
        
        return result
    
    @staticmethod
    def comprehensive_validate(entry: Dict, result: Dict, result_source: str = 'unknown') -> Dict:
        """
        综合验证BibTeX条目和搜索结果
        
        Args:
            entry: BibTeX条目字典，包含 title, authors, year, doi 等
            result: 搜索结果字典，格式取决于数据源
            result_source: 数据源名称 ('arxiv', 'crossref', 'openreview', 'scholar')
            
        Returns:
            详细的验证结果字典
        """
        validation_result = {
            'source': result_source,
            'overall_match': False,
            'field_validations': {},
            'issues': [],
            'warnings': [],
            'confidence': 0.0,
            'is_hallucination': False
        }
        
        # 提取结果信息（根据数据源）
        result_title = ""
        result_authors = []
        result_year = None
        result_doi = None
        
        if result_source == 'arxiv':
            result_title = result.get('title', '')
            result_authors = [str(a) for a in result.get('authors', [])]
            if result.get('published'):
                result_year = str(result.published.year)
            result_doi = result.get('doi')
        elif result_source == 'crossref':
            result_title = result.get('title', [''])[0] if result.get('title') else ''
            if result.get('author'):
                result_authors = []
                for author in result['author']:
                    family = author.get('family', '')
                    given = author.get('given', '')
                    if family:
                        if given:
                            result_authors.append(f"{family}, {given}")
                        else:
                            result_authors.append(family)
            if result.get('published-print'):
                pub_dates = result['published-print'].get('date-parts', [])
                if pub_dates and len(pub_dates[0]) > 0:
                    result_year = str(pub_dates[0][0])
            elif result.get('published-online'):
                pub_dates = result['published-online'].get('date-parts', [])
                if pub_dates and len(pub_dates[0]) > 0:
                    result_year = str(pub_dates[0][0])
            result_doi = result.get('DOI')
        elif result_source == 'openreview':
            result_title = result.get('content', {}).get('title', '')
            result_authors = result.get('content', {}).get('authors', [])
            if result.get('cdate'):
                result_year = str(result['cdate'] // 10000000000)
        elif result_source == 'scholar':
            result_title = result.get('title', '')
            result_authors = result.get('authors', [])
            if result.get('year'):
                result_year = str(result['year'])
        
        # 字段级验证
        # 1. 标题验证
        title_validation = DetailedValidator.validate_title(
            entry.get('title', ''),
            result_title
        )
        validation_result['field_validations']['title'] = title_validation
        if title_validation.get('issue'):
            validation_result['issues'].append(f"标题: {title_validation['issue']}")
        if title_validation.get('warning'):
            validation_result['warnings'].append(f"标题: {title_validation['warning']}")
        
        # 2. 作者验证
        author_validation = DetailedValidator.validate_authors(
            entry.get('authors', []),
            result_authors
        )
        validation_result['field_validations']['authors'] = author_validation
        for issue in author_validation.get('issues', []):
            validation_result['issues'].append(f"作者: {issue}")
        
        # 3. 年份验证
        year_validation = DetailedValidator.validate_year(
            entry.get('year'),
            result_year
        )
        validation_result['field_validations']['year'] = year_validation
        if year_validation.get('issue'):
            validation_result['issues'].append(f"年份: {year_validation['issue']}")
        if year_validation.get('warning'):
            validation_result['warnings'].append(f"年份: {year_validation['warning']}")
        
        # 4. DOI验证（如果有）
        if entry.get('doi') or result_doi:
            doi_validation = DetailedValidator.validate_doi(
                entry.get('doi'),
                result_doi
            )
            validation_result['field_validations']['doi'] = doi_validation
            if doi_validation.get('issue'):
                validation_result['issues'].append(f"DOI: {doi_validation['issue']}")
        
        # 计算综合匹配度和置信度
        field_scores = []
        
        if title_validation.get('match'):
            field_scores.append(title_validation.get('similarity', 0.5))
        else:
            field_scores.append(0.0)
        
        if author_validation.get('match'):
            # 作者匹配分数基于匹配比例
            author_score = author_validation.get('match_ratio', 0.0)
            # 完全匹配的权重更高
            exact_ratio = author_validation.get('exact_match_count', 0) / max(author_validation.get('total_entry', 1), 1)
            author_score = author_score * 0.7 + exact_ratio * 0.3
            field_scores.append(author_score)
        else:
            field_scores.append(0.0)
        
        if year_validation.get('match'):
            field_scores.append(1.0)
        else:
            field_scores.append(0.5)  # 年份不匹配不完全否定
        
        # 综合分数（标题权重最高）
        if field_scores:
            validation_result['confidence'] = (
                field_scores[0] * 0.5 +  # 标题
                field_scores[1] * 0.4 +  # 作者
                field_scores[2] * 0.1    # 年份
            )
        
        # 判断是否匹配
        # 标题必须匹配，且作者至少50%匹配
        validation_result['overall_match'] = (
            title_validation.get('match', False) and
            author_validation.get('match', False) and
            validation_result['confidence'] >= 0.5
        )
        
        # 判断是否是幻觉
        # 如果标题匹配但作者大部分不匹配，可能是幻觉
        if title_validation.get('match') and not author_validation.get('match'):
            if author_validation.get('match_ratio', 0.0) < 0.3:
                validation_result['is_hallucination'] = True
                validation_result['issues'].append('⚠️ 可能的幻觉: 标题匹配但大部分作者不匹配')
        
        # 如果标题和第一作者匹配，但其他作者都不匹配，可能是幻觉
        if (title_validation.get('match') and 
            author_validation.get('exact_match_count', 0) == 1 and
            author_validation.get('total_entry', 0) > 2):
            validation_result['is_hallucination'] = True
            validation_result['issues'].append('⚠️ 可能的幻觉: 标题和第一作者匹配，但其他作者不匹配')
        
        return validation_result
