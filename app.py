#!/usr/bin/env python3
"""
LLM参考文献幻觉检测工具 - Streamlit Web界面
"""
import streamlit as st
import tempfile
import os
from pathlib import Path
from ref_checker.bibtex_parser import BibTeXParser
from ref_checker.validator import ReferenceValidator
from ref_checker.report_generator import MarkdownReportGenerator
import logging

# 配置页面
st.set_page_config(
    page_title="LLM参考文献幻觉检测工具",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 配置日志
logging.basicConfig(level=logging.WARNING)  # 减少日志输出

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stats-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .danger-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<div class="main-header">🔍 LLM参考文献幻觉检测工具</div>', unsafe_allow_html=True)
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    ### 功能特点
    - ✅ 验证 BibTeX 参考文献的真实性
    - 📊 生成详细的验证报告
    - 🔍 检测可能的幻觉条目
    - 📈 提供置信度评分
    
    ### 使用步骤
    1. 上传或粘贴 BibTeX 文件
    2. 点击"开始验证"按钮
    3. 查看验证结果和报告
    
    ### 支持格式
    - BibTeX (.bib) 文件
    - 标准 BibTeX 格式文本
    """)
    
    st.markdown("---")
    st.markdown("""
    ### 📝 关于
    本工具用于检测 LLM 生成的参考文献中可能存在的幻觉，
    确保论文参考文献的准确性。
    
    **版本**: 0.1.0
    """)

# 主界面
tab1, tab2 = st.tabs(["📁 文件上传", "📝 文本输入"])

with tab1:
    st.subheader("上传 BibTeX 文件")
    uploaded_file = st.file_uploader(
        "选择 BibTeX 文件 (.bib)",
        type=['bib'],
        help="上传你的 BibTeX 参考文献文件"
    )
    
    if uploaded_file is not None:
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bib', mode='w', encoding='utf-8') as tmp_file:
            tmp_file.write(uploaded_file.read().decode('utf-8'))
            tmp_file_path = tmp_file.name
        
        st.success(f"✅ 文件已上传: {uploaded_file.name}")
        
        if st.button("🚀 开始验证", type="primary", use_container_width=True):
            with st.spinner("正在验证参考文献，请稍候..."):
                try:
                    # 解析文件
                    parser = BibTeXParser()
                    entries = parser.parse_file(tmp_file_path)
                    
                    if not entries:
                        st.error("❌ 未找到任何参考文献条目")
                    else:
                        st.info(f"📚 找到 {len(entries)} 条参考文献，开始验证...")
                        
                        # 验证
                        validator = ReferenceValidator()
                        results = validator.validate_batch(entries)
                        
                        # 统计
                        total = len(results)
                        valid_count = sum(1 for r in results if r.is_valid)
                        suspicious_count = sum(1 for r in results if r.is_suspicious)
                        needs_review_count = total - valid_count - suspicious_count
                        avg_confidence = sum(r.confidence for r in results) / total if total > 0 else 0.0
                        
                        # 显示统计
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("总参考文献数", total)
                        with col2:
                            st.metric("✅ 验证通过", valid_count, f"{valid_count/total*100:.1f}%")
                        with col3:
                            st.metric("⚠️ 存在疑问", suspicious_count, f"{suspicious_count/total*100:.1f}%")
                        with col4:
                            st.metric("🔍 需要复查", needs_review_count, f"{needs_review_count/total*100:.1f}%")
                        
                        st.metric("平均置信度", f"{avg_confidence:.2%}")
                        
                        # 详细结果
                        st.markdown("---")
                        st.subheader("📋 详细验证结果")
                        
                        for idx, result in enumerate(results, 1):
                            # 状态图标
                            if result.is_valid:
                                status_icon = "✅"
                                status_color = "success"
                            elif result.is_suspicious:
                                status_icon = "⚠️"
                                status_color = "warning"
                            else:
                                status_icon = "🔍"
                                status_color = "info"
                            
                            with st.expander(f"{status_icon} {idx}. {result.entry.cite_key} - {result.recommendation}", expanded=False):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**基本信息:**")
                                    st.write(f"- **标题**: {result.entry.title or '未提供'}")
                                    st.write(f"- **作者**: {', '.join(result.entry.authors) if result.entry.authors else '未提供'}")
                                    st.write(f"- **年份**: {result.entry.year or '未提供'}")
                                    if result.entry.journal:
                                        st.write(f"- **期刊/会议**: {result.entry.journal}")
                                    if result.entry.doi:
                                        st.write(f"- **DOI**: {result.entry.doi}")
                                    if result.entry.arxiv_id:
                                        st.write(f"- **ArXiv ID**: {result.entry.arxiv_id}")
                                
                                with col2:
                                    st.markdown("**验证结果:**")
                                    st.write(f"- **状态**: {result.recommendation}")
                                    st.write(f"- **置信度**: {result.confidence:.2%}")
                                    
                                    # 验证源信息
                                    if result.verification_sources:
                                        st.markdown("**验证源信息:**")
                                        for source, source_result in result.verification_sources.items():
                                            if source_result.get('found', False):
                                                st.success(f"✅ {source.upper()}: 找到匹配")
                                                if source_result.get('arxiv_id'):
                                                    arxiv_id = source_result['arxiv_id']
                                                    st.markdown(f"   - [ArXiv链接](https://arxiv.org/abs/{arxiv_id})")
                                            else:
                                                st.error(f"❌ {source.upper()}: 未找到匹配")
                                
                                # 问题和警告
                                if result.issues:
                                    st.markdown("**❌ 发现的问题:**")
                                    for issue in result.issues:
                                        st.error(f"- {issue}")
                                
                                if result.warnings:
                                    st.markdown("**⚠️ 警告:**")
                                    for warning in result.warnings:
                                        st.warning(f"- {warning}")
                        
                        # 生成报告
                        st.markdown("---")
                        st.subheader("📄 生成报告")
                        report_generator = MarkdownReportGenerator()
                        report_content = report_generator.generate_report(results)
                        
                        # 下载按钮
                        st.download_button(
                            label="📥 下载 Markdown 报告",
                            data=report_content,
                            file_name=f"{Path(uploaded_file.name).stem}_report.md",
                            mime="text/markdown"
                        )
                        
                        # 显示报告预览
                        with st.expander("📖 查看报告预览"):
                            st.markdown(report_content)
                        
                        # 清理临时文件
                        os.unlink(tmp_file_path)
                        
                except Exception as e:
                    st.error(f"❌ 验证过程中出错: {str(e)}")
                    import traceback
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())
                    if 'tmp_file_path' in locals():
                        os.unlink(tmp_file_path)

with tab2:
    st.subheader("粘贴 BibTeX 文本")
    bibtex_text = st.text_area(
        "输入 BibTeX 格式的参考文献",
        height=300,
        help="直接粘贴你的 BibTeX 参考文献内容",
        placeholder="""@article{example2023,
  title={Example Paper Title},
  author={Author, First and Author, Second},
  journal={Example Journal},
  year={2023}
}"""
    )
    
    if st.button("🚀 开始验证", type="primary", use_container_width=True, key="validate_text"):
        if not bibtex_text.strip():
            st.warning("⚠️ 请输入 BibTeX 内容")
        else:
            with st.spinner("正在验证参考文献，请稍候..."):
                try:
                    # 解析文本
                    parser = BibTeXParser()
                    entries = parser.parse_string(bibtex_text)
                    
                    if not entries:
                        st.error("❌ 未找到任何参考文献条目")
                    else:
                        st.info(f"📚 找到 {len(entries)} 条参考文献，开始验证...")
                        
                        # 验证
                        validator = ReferenceValidator()
                        results = validator.validate_batch(entries)
                        
                        # 统计（与文件上传相同的显示逻辑）
                        total = len(results)
                        valid_count = sum(1 for r in results if r.is_valid)
                        suspicious_count = sum(1 for r in results if r.is_suspicious)
                        needs_review_count = total - valid_count - suspicious_count
                        avg_confidence = sum(r.confidence for r in results) / total if total > 0 else 0.0
                        
                        # 显示统计
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("总参考文献数", total)
                        with col2:
                            st.metric("✅ 验证通过", valid_count, f"{valid_count/total*100:.1f}%")
                        with col3:
                            st.metric("⚠️ 存在疑问", suspicious_count, f"{suspicious_count/total*100:.1f}%")
                        with col4:
                            st.metric("🔍 需要复查", needs_review_count, f"{needs_review_count/total*100:.1f}%")
                        
                        st.metric("平均置信度", f"{avg_confidence:.2%}")
                        
                        # 详细结果（与文件上传相同的显示逻辑）
                        st.markdown("---")
                        st.subheader("📋 详细验证结果")
                        
                        for idx, result in enumerate(results, 1):
                            if result.is_valid:
                                status_icon = "✅"
                            elif result.is_suspicious:
                                status_icon = "⚠️"
                            else:
                                status_icon = "🔍"
                            
                            with st.expander(f"{status_icon} {idx}. {result.entry.cite_key} - {result.recommendation}", expanded=False):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**基本信息:**")
                                    st.write(f"- **标题**: {result.entry.title or '未提供'}")
                                    st.write(f"- **作者**: {', '.join(result.entry.authors) if result.entry.authors else '未提供'}")
                                    st.write(f"- **年份**: {result.entry.year or '未提供'}")
                                    if result.entry.journal:
                                        st.write(f"- **期刊/会议**: {result.entry.journal}")
                                    if result.entry.arxiv_id:
                                        st.write(f"- **ArXiv ID**: {result.entry.arxiv_id}")
                                
                                with col2:
                                    st.markdown("**验证结果:**")
                                    st.write(f"- **状态**: {result.recommendation}")
                                    st.write(f"- **置信度**: {result.confidence:.2%}")
                                    
                                    if result.verification_sources:
                                        st.markdown("**验证源信息:**")
                                        for source, source_result in result.verification_sources.items():
                                            if source_result.get('found', False):
                                                st.success(f"✅ {source.upper()}: 找到匹配")
                                                if source_result.get('arxiv_id'):
                                                    arxiv_id = source_result['arxiv_id']
                                                    st.markdown(f"   - [ArXiv链接](https://arxiv.org/abs/{arxiv_id})")
                                            else:
                                                st.error(f"❌ {source.upper()}: 未找到匹配")
                                
                                if result.issues:
                                    st.markdown("**❌ 发现的问题:**")
                                    for issue in result.issues:
                                        st.error(f"- {issue}")
                                
                                if result.warnings:
                                    st.markdown("**⚠️ 警告:**")
                                    for warning in result.warnings:
                                        st.warning(f"- {warning}")
                        
                        # 生成报告
                        st.markdown("---")
                        st.subheader("📄 生成报告")
                        report_generator = MarkdownReportGenerator()
                        report_content = report_generator.generate_report(results)
                        
                        st.download_button(
                            label="📥 下载 Markdown 报告",
                            data=report_content,
                            file_name="references_report.md",
                            mime="text/markdown"
                        )
                        
                        with st.expander("📖 查看报告预览"):
                            st.markdown(report_content)
                
                except Exception as e:
                    st.error(f"❌ 验证过程中出错: {str(e)}")
                    import traceback
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>LLM参考文献幻觉检测工具 v0.1.0 | 
    <a href="https://github.com/JijiKing-Sam/LLM-Ref-Check" target="_blank">GitHub</a></p>
</div>
""", unsafe_allow_html=True)
