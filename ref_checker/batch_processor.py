"""
批量处理模块
为后期批量处理功能预留接口
"""
from typing import List, Dict, Iterator
from pathlib import Path
import logging
from .bibtex_parser import BibTeXParser
from .validator import ReferenceValidator
from .report_generator import MarkdownReportGenerator

logger = logging.getLogger(__name__)


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self):
        """初始化批量处理器"""
        self.parser = BibTeXParser()
        self.validator = ReferenceValidator()
        self.report_generator = MarkdownReportGenerator()
    
    def process_directory(self, input_dir: Path, output_dir: Path, 
                         pattern: str = "*.bib") -> List[Dict]:
        """
        处理目录中的所有BibTeX文件
        
        Args:
            input_dir: 输入目录路径
            output_dir: 输出目录路径
            pattern: 文件匹配模式
            
        Returns:
            处理结果列表
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        bib_files = list(input_path.glob(pattern))
        results = []
        
        for bib_file in bib_files:
            try:
                result = self.process_single_file(bib_file, output_path)
                results.append(result)
            except Exception as e:
                logger.error(f"处理文件 {bib_file} 时出错: {e}")
                results.append({
                    'file': str(bib_file),
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def process_single_file(self, bib_file: Path, output_dir: Path) -> Dict:
        """
        处理单个BibTeX文件
        
        Args:
            bib_file: BibTeX文件路径
            output_dir: 输出目录路径
            
        Returns:
            处理结果字典
        """
        logger.info(f"处理文件: {bib_file}")
        
        # 解析
        entries = self.parser.parse_file(str(bib_file))
        
        # 验证
        validation_results = self.validator.validate_batch(entries)
        
        # 生成报告
        output_file = output_dir / f"{bib_file.stem}_report.md"
        self.report_generator.generate_report(validation_results, str(output_file))
        
        # 统计
        valid_count = sum(1 for r in validation_results if r.is_valid)
        suspicious_count = sum(1 for r in validation_results if r.is_suspicious)
        
        return {
            'file': str(bib_file),
            'status': 'success',
            'total_entries': len(entries),
            'valid_count': valid_count,
            'suspicious_count': suspicious_count,
            'output_file': str(output_file)
        }
    
    def process_file_list(self, file_list: List[Path], output_dir: Path) -> List[Dict]:
        """
        处理文件列表
        
        Args:
            file_list: BibTeX文件路径列表
            output_dir: 输出目录路径
            
        Returns:
            处理结果列表
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        for bib_file in file_list:
            try:
                result = self.process_single_file(bib_file, output_path)
                results.append(result)
            except Exception as e:
                logger.error(f"处理文件 {bib_file} 时出错: {e}")
                results.append({
                    'file': str(bib_file),
                    'status': 'error',
                    'error': str(e)
                })
        
        return results




