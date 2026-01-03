#!/usr/bin/env python3
"""
LLM参考文献幻觉检测工具 - 主程序入口
"""
import argparse
import sys
import logging
from pathlib import Path
from ref_checker.bibtex_parser import BibTeXParser
from ref_checker.validator import ReferenceValidator
from ref_checker.report_generator import MarkdownReportGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='LLM参考文献幻觉检测工具 - 验证BibTeX参考文献的真实性'
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='输入的BibTeX文件路径'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='输出报告文件路径（默认为输入文件名_report.md）'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细日志信息'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 检查输入文件是否存在
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"输入文件不存在: {input_path}")
        sys.exit(1)
    
    # 确定输出文件路径
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}_report.md"
    
    logger.info(f"开始验证参考文献文件: {input_path}")
    
    try:
        # 1. 解析BibTeX文件
        logger.info("正在解析BibTeX文件...")
        parser_obj = BibTeXParser()
        entries = parser_obj.parse_file(str(input_path))
        
        if not entries:
            logger.warning("未找到任何参考文献条目")
            sys.exit(0)
        
        logger.info(f"成功解析 {len(entries)} 条参考文献")
        
        # 2. 验证参考文献
        logger.info("开始验证参考文献...")
        validator = ReferenceValidator()
        results = validator.validate_batch(entries)
        
        # 3. 生成报告
        logger.info("正在生成验证报告...")
        report_generator = MarkdownReportGenerator()
        report_content = report_generator.generate_report(results, str(output_path))
        
        logger.info(f"验证完成！报告已保存到: {output_path}")
        
        # 打印简要统计
        valid_count = sum(1 for r in results if r.is_valid)
        suspicious_count = sum(1 for r in results if r.is_suspicious)
        
        print("\n" + "="*50)
        print("验证摘要:")
        print(f"  总参考文献数: {len(results)}")
        print(f"  ✅ 验证通过: {valid_count}")
        print(f"  ⚠️  存在疑问: {suspicious_count}")
        print(f"  🔍 需要复查: {len(results) - valid_count - suspicious_count}")
        print("="*50)
        print(f"\n详细报告请查看: {output_path}")
        
    except Exception as e:
        logger.error(f"处理过程中出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()



