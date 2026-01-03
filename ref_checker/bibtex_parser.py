"""
BibTeX文件解析器
"""
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BibTeXEntry:
    """表示一条BibTeX参考文献条目"""
    
    def __init__(self, entry: Dict):
        self.entry = entry
        self.entry_type = entry.get('ENTRYTYPE', '').lower()
        self.cite_key = entry.get('ID', '')
        
    @property
    def title(self) -> Optional[str]:
        """获取标题"""
        return self.entry.get('title', '').strip().strip('{}')
    
    @property
    def authors(self) -> List[str]:
        """获取作者列表"""
        authors_str = self.entry.get('author', '')
        if not authors_str:
            return []
        # 处理BibTeX作者格式 (用and分隔)
        authors = [a.strip() for a in authors_str.split(' and ')]
        return authors
    
    @property
    def year(self) -> Optional[str]:
        """获取年份"""
        return self.entry.get('year', '').strip()
    
    @property
    def journal(self) -> Optional[str]:
        """获取期刊名称"""
        return self.entry.get('journal', '') or self.entry.get('booktitle', '')
    
    @property
    def doi(self) -> Optional[str]:
        """获取DOI"""
        return self.entry.get('doi', '').strip()
    
    @property
    def arxiv_id(self) -> Optional[str]:
        """获取arXiv ID"""
        import re
        
        # 方法1: 从eprint字段提取
        eprint = self.entry.get('eprint', '')
        if eprint:
            if 'arxiv' in eprint.lower():
                # 提取arXiv ID (格式: arxiv:1706.03762 或 arXiv:1706.03762)
                match = re.search(r'arxiv:([0-9.]+)', eprint, re.IGNORECASE)
                if match:
                    return match.group(1)
            # 如果eprint直接是arXiv ID格式
            elif re.match(r'^[0-9]{4}\.[0-9]{4,5}(v[0-9]+)?$', eprint):
                return eprint.split('v')[0]  # 移除版本号
        
        # 方法2: 从journal字段提取 (例如: arXiv preprint arXiv:1706.03762)
        journal = self.entry.get('journal', '')
        if journal and 'arxiv' in journal.lower():
            match = re.search(r'arxiv[:\s]+([0-9]{4}\.[0-9]{4,5})', journal, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @property
    def url(self) -> Optional[str]:
        """获取URL"""
        return self.entry.get('url', '').strip()
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'cite_key': self.cite_key,
            'entry_type': self.entry_type,
            'title': self.title,
            'authors': self.authors,
            'year': self.year,
            'journal': self.journal,
            'doi': self.doi,
            'arxiv_id': self.arxiv_id,
            'url': self.url,
            'raw_entry': self.entry
        }


class BibTeXParser:
    """BibTeX文件解析器"""
    
    def __init__(self):
        self.parser = BibTexParser()
        self.parser.customization = convert_to_unicode
        self.parser.ignore_nonstandard_types = False
        self.parser.homogenise_fields = True
    
    def parse_file(self, file_path: str) -> List[BibTeXEntry]:
        """
        解析BibTeX文件
        
        Args:
            file_path: BibTeX文件路径
            
        Returns:
            参考文献条目列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                bib_database = bibtexparser.load(f, parser=self.parser)
            
            entries = []
            for entry_dict in bib_database.entries:
                entry = BibTeXEntry(entry_dict)
                entries.append(entry)
            
            logger.info(f"成功解析 {len(entries)} 条参考文献")
            return entries
            
        except Exception as e:
            logger.error(f"解析BibTeX文件失败: {e}")
            raise
    
    def parse_string(self, bibtex_string: str) -> List[BibTeXEntry]:
        """
        解析BibTeX字符串
        
        Args:
            bibtex_string: BibTeX格式的字符串
            
        Returns:
            参考文献条目列表
        """
        try:
            bib_database = bibtexparser.loads(bibtex_string, parser=self.parser)
            
            entries = []
            for entry_dict in bib_database.entries:
                entry = BibTeXEntry(entry_dict)
                entries.append(entry)
            
            logger.info(f"成功解析 {len(entries)} 条参考文献")
            return entries
            
        except Exception as e:
            logger.error(f"解析BibTeX字符串失败: {e}")
            raise
