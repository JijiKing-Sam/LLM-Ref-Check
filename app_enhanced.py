#!/usr/bin/env python3
"""
LLM参考文献幻觉检测工具 - 增强版 Streamlit Web界面
融合了现代化可视化设计理念
"""
import streamlit as st
import tempfile
import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ref_checker.bibtex_parser import BibTeXParser
try:
    from ref_checker.multi_validator import MultiSourceValidator as ReferenceValidator
    MULTI_SOURCE = True
except ImportError:
    from ref_checker.validator import ReferenceValidator
    MULTI_SOURCE = False
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
logging.basicConfig(level=logging.WARNING)

# 增强的CSS样式 - 融合React应用的设计理念
st.markdown("""
<style>
    /* 主标题样式 */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1e40af 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* 统计卡片样式 */
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* 状态徽章样式 */
    .badge-supported {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-size: 0.75rem;
        font-weight: 500;
        background-color: #dcfce7;
        color: #166534;
    }
    
    .badge-contradicted {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-size: 0.75rem;
        font-weight: 500;
        background-color: #fee2e2;
        color: #991b1b;
    }
    
    .badge-neutral {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-size: 0.75rem;
        font-weight: 500;
        background-color: #fef3c7;
        color: #92400e;
    }
    
    /* 进度条样式 */
    .progress-bar {
        width: 100%;
        height: 0.5rem;
        background-color: #f1f5f9;
        border-radius: 9999px;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 9999px;
        transition: width 0.3s ease;
    }
    
    /* 句子卡片样式 */
    .sentence-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.75rem;
        border: 1px solid;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .sentence-card:hover {
        transform: translateX(4px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .sentence-card-supported {
        background-color: #f0fdf4;
        border-color: #86efac;
    }
    
    .sentence-card-contradicted {
        background-color: #fef2f2;
        border-color: #fca5a5;
    }
    
    .sentence-card-neutral {
        background-color: #fffbeb;
        border-color: #fde047;
    }
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'validation_results' not in st.session_state:
    st.session_state.validation_results = None
if 'selected_entry_idx' not in st.session_state:
    st.session_state.selected_entry_idx = None

# 标题
st.markdown('<div class="main-header">🔍 LLM参考文献幻觉检测工具</div>', unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #64748b; margin-bottom: 2rem;'>
验证 BibTeX 参考文献的真实性，检测可能的幻觉条目，确保论文参考文献的准确性
</div>
""", unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    ### 功能特点
    - ✅ 验证 BibTeX 参考文献的真实性
    - 📊 生成详细的验证报告
    - 🔍 检测可能的幻觉条目
    - 📈 提供置信度评分
    - 📊 可视化统计图表
    
    ### 使用步骤
    1. 上传或粘贴 BibTeX 文件
    2. 点击"开始验证"按钮
    3. 查看验证结果和可视化图表
    4. 点击条目查看详细信息
    
    ### 支持格式
    - BibTeX (.bib) 文件
    - 标准 BibTeX 格式文本
    """)
    
    st.markdown("---")
    st.markdown("""
    ### 📝 关于
    本工具用于检测 LLM 生成的参考文献中可能存在的幻觉，
    确保论文参考文献的准确性。
    
    **版本**: 0.2.0 (Enhanced)
    """)
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center;'>
    <a href="https://github.com/JijiKing-Sam/LLM-Ref-Check" target="_blank" style='text-decoration: none; color: #64748b;'>
    🔗 View on GitHub
    </a>
    </div>
    """, unsafe_allow_html=True)

# 主界面
tab1, tab2 = st.tabs(["📁 文件上传", "📝 文本输入"])

def create_summary_cards(results):
    """创建统计卡片"""
    total = len(results)
    valid_count = sum(1 for r in results if r.is_valid)
    suspicious_count = sum(1 for r in results if r.is_suspicious)
    needs_review_count = total - valid_count - suspicious_count
    avg_confidence = sum(r.confidence for r in results) / total if total > 0 else 0.0
    
    # 可靠性分数
    reliability_score = int((valid_count / total) * 100) if total > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div style='display: flex; align-items: center; gap: 1rem;'>
                <div style='padding: 0.75rem; border-radius: 9999px; background-color: {'#dcfce7' if reliability_score > 70 else '#fef3c7'};'>
                    <span style='font-size: 1.5rem; color: {'#166534' if reliability_score > 70 else '#92400e'};'>📊</span>
                </div>
                <div>
                    <p style='margin: 0; font-size: 0.875rem; color: #64748b; font-weight: 500;'>Reliability Score</p>
                    <p style='margin: 0; font-size: 1.5rem; font-weight: bold; color: #1e293b;'>{reliability_score}%</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div style='margin-bottom: 0.5rem;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;'>
                    <span style='font-size: 0.875rem; color: #64748b;'>✅ Verified</span>
                    <span style='font-size: 0.875rem; font-weight: bold; color: #16a34a;'>{valid_count}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style='width: {(valid_count/total)*100 if total > 0 else 0}%; background-color: #22c55e;'></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div style='margin-bottom: 0.5rem;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;'>
                    <span style='font-size: 0.875rem; color: #64748b;'>⚠️ Suspicious</span>
                    <span style='font-size: 0.875rem; font-weight: bold; color: #dc2626;'>{suspicious_count}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style='width: {(suspicious_count/total)*100 if total > 0 else 0}%; background-color: #ef4444;'></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div style='margin-bottom: 0.5rem;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;'>
                    <span style='font-size: 0.875rem; color: #64748b;'>🔍 Needs Review</span>
                    <span style='font-size: 0.875rem; font-weight: bold; color: #ca8a04;'>{needs_review_count}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style='width: {(needs_review_count/total)*100 if total > 0 else 0}%; background-color: #eab308;'></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    return {
        'total': total,
        'valid_count': valid_count,
        'suspicious_count': suspicious_count,
        'needs_review_count': needs_review_count,
        'avg_confidence': avg_confidence,
        'reliability_score': reliability_score
    }

def create_visualization_charts(stats, results):
    """创建可视化图表"""
    # 饼图 - 验证状态分布
    status_counts = {
        'Verified': stats['valid_count'],
        'Suspicious': stats['suspicious_count'],
        'Needs Review': stats['needs_review_count']
    }
    
    fig_pie = px.pie(
        values=list(status_counts.values()),
        names=list(status_counts.keys()),
        title="验证状态分布",
        color_discrete_map={
            'Verified': '#22c55e',
            'Suspicious': '#ef4444',
            'Needs Review': '#eab308'
        }
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(height=300, showlegend=True)
    
    # 置信度分布直方图
    confidences = [r.confidence * 100 for r in results]
    fig_hist = px.histogram(
        x=confidences,
        nbins=20,
        title="置信度分布",
        labels={'x': '置信度 (%)', 'y': '数量'},
        color_discrete_sequence=['#3b82f6']
    )
    fig_hist.update_layout(height=300, showlegend=False)
    
    return fig_pie, fig_hist

def display_results(results):
    """显示验证结果"""
    stats = create_summary_cards(results)
    
    st.markdown("---")
    
    # 可视化图表
    st.subheader("📊 可视化分析")
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pie, _ = create_visualization_charts(stats, results)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        _, fig_hist = create_visualization_charts(stats, results)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    st.markdown("---")
    
    # 详细结果 - 分栏显示
    st.subheader("📋 详细验证结果")
    
    col_left, col_right = st.columns([7, 5])
    
    with col_left:
        st.markdown("**分析结果**")
        for idx, result in enumerate(results):
            # 状态图标和样式
            if result.is_valid:
                status_icon = "✅"
                status_badge = '<span class="badge-supported">Verified</span>'
                card_class = "sentence-card sentence-card-supported"
            elif result.is_suspicious:
                status_icon = "⚠️"
                status_badge = '<span class="badge-contradicted">Suspicious</span>'
                card_class = "sentence-card sentence-card-contradicted"
            else:
                status_icon = "🔍"
                status_badge = '<span class="badge-neutral">Needs Review</span>'
                card_class = "sentence-card sentence-card-neutral"
            
            # 创建可点击的卡片
            clicked = st.button(
                f"{status_icon} {result.entry.cite_key}",
                key=f"btn_{idx}",
                use_container_width=True
            )
            
            if clicked:
                st.session_state.selected_entry_idx = idx
            
            # 显示卡片内容
            st.markdown(f"""
            <div class="{card_class}">
                <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;'>
                    {status_badge}
                    <span style='font-size: 0.75rem; color: #94a3b8; font-family: monospace;'>ID: {idx}</span>
                </div>
                <p style='margin: 0; color: #1e293b; line-height: 1.6;'><strong>{result.entry.title or '未提供标题'}</strong></p>
                <p style='margin: 0.25rem 0 0 0; color: #64748b; font-size: 0.875rem;'>
                    {', '.join(result.entry.authors[:3]) if result.entry.authors else '未知作者'}
                    {f"({result.entry.year})" if result.entry.year else ""}
                </p>
                <div style='margin-top: 0.5rem; display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 0.75rem; color: #64748b;'>置信度</span>
                    <div style='display: flex; align-items: center; gap: 0.5rem;'>
                        <div style='width: 80px; height: 0.5rem; background-color: #f1f5f9; border-radius: 9999px; overflow: hidden;'>
                            <div style='width: {result.confidence * 100}%; height: 100%; background-color: #3b82f6; border-radius: 9999px;'></div>
                        </div>
                        <span style='font-size: 0.75rem; font-weight: bold; color: #1e293b;'>{result.confidence:.0%}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_right:
        st.markdown("**详细信息**")
        if st.session_state.selected_entry_idx is not None:
            selected = results[st.session_state.selected_entry_idx]
            
            st.markdown(f"""
            <div style='background: white; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; margin-bottom: 1rem;'>
                <span style='font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; font-weight: bold; display: block; margin-bottom: 0.5rem;'>Selected Entry</span>
                <p style='font-size: 1rem; color: #1e293b; font-weight: 500; margin: 0;'>{selected.entry.title or '未提供'}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 基本信息
            with st.expander("📝 基本信息", expanded=True):
                st.write(f"**标题**: {selected.entry.title or '未提供'}")
                st.write(f"**作者**: {', '.join(selected.entry.authors) if selected.entry.authors else '未提供'}")
                st.write(f"**年份**: {selected.entry.year or '未提供'}")
                if selected.entry.journal:
                    st.write(f"**期刊/会议**: {selected.entry.journal}")
                if selected.entry.doi:
                    st.write(f"**DOI**: {selected.entry.doi}")
                if selected.entry.arxiv_id:
                    st.write(f"**ArXiv ID**: [{selected.entry.arxiv_id}](https://arxiv.org/abs/{selected.entry.arxiv_id})")
            
            # 验证结果
            with st.expander("🔍 验证结果", expanded=True):
                st.write(f"**状态**: {selected.recommendation}")
                st.write(f"**置信度**: {selected.confidence:.2%}")
                
                if selected.verification_sources:
                    st.markdown("**验证源信息:**")
                    source_names = {
                        'arxiv': 'ArXiv',
                        'crossref': 'Crossref',
                        'openreview': 'OpenReview',
                        'scholar': 'Google Scholar'
                    }
                    found_count = 0
                    for source, source_result in selected.verification_sources.items():
                        source_display = source_names.get(source, source.upper())
                        if source_result.get('found', False):
                            found_count += 1
                            st.success(f"✅ {source_display}: 找到匹配")
                            # 显示链接
                            if source_result.get('source_url'):
                                st.markdown(f"   - [查看原文]({source_result['source_url']})")
                            elif source_result.get('arxiv_id'):
                                arxiv_id = source_result['arxiv_id']
                                st.markdown(f"   - [ArXiv链接](https://arxiv.org/abs/{arxiv_id})")
                            elif source_result.get('source_id'):
                                source_id = source_result['source_id']
                                if source == 'crossref':
                                    st.markdown(f"   - [DOI链接](https://doi.org/{source_id})")
                                elif source == 'openreview':
                                    st.markdown(f"   - [OpenReview链接](https://openreview.net/forum?id={source_id})")
                            
                            # 显示匹配详情
                            match_details = source_result.get('match_details', {})
                            if match_details:
                                matches = []
                                if match_details.get('title_match'):
                                    matches.append("标题匹配")
                                if match_details.get('author_match'):
                                    matches.append("作者匹配")
                                if match_details.get('year_match'):
                                    matches.append("年份匹配")
                                if matches:
                                    st.caption(f"   匹配项: {', '.join(matches)}")
                        else:
                            st.error(f"❌ {source_display}: 未找到匹配")
                            if source_result.get('error'):
                                st.caption(f"   错误: {source_result['error']}")
                    
                    # 显示源数量统计
                    total_count = len(selected.verification_sources)
                    if total_count > 1:
                        st.info(f"📊 验证源统计: {found_count}/{total_count} 个源找到匹配")
                        if hasattr(selected, 'source_count'):
                            st.caption(f"   多源验证: {selected.source_count} 个源确认")
            
            # 问题和警告
            if selected.issues:
                with st.expander("❌ 发现的问题", expanded=True):
                    for issue in selected.issues:
                        st.error(f"- {issue}")
            
            if selected.warnings:
                with st.expander("⚠️ 警告", expanded=True):
                    for warning in selected.warnings:
                        st.warning(f"- {warning}")
        else:
            st.info("👈 点击左侧条目查看详细信息")

# 文件上传标签页
with tab1:
    st.subheader("上传 BibTeX 文件")
    uploaded_file = st.file_uploader(
        "选择 BibTeX 文件 (.bib)",
        type=['bib'],
        help="上传你的 BibTeX 参考文献文件"
    )
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bib', mode='w', encoding='utf-8') as tmp_file:
            tmp_file.write(uploaded_file.read().decode('utf-8'))
            tmp_file_path = tmp_file.name
        
        st.success(f"✅ 文件已上传: {uploaded_file.name}")
        
        if st.button("🚀 开始验证", type="primary", use_container_width=True):
            with st.spinner("正在验证参考文献，请稍候..."):
                try:
                    parser = BibTeXParser()
                    entries = parser.parse_file(tmp_file_path)
                    
                    if not entries:
                        st.error("❌ 未找到任何参考文献条目")
                    else:
                        st.info(f"📚 找到 {len(entries)} 条参考文献，开始验证...")
                        
                        # 使用多源验证器（如果可用）
                        try:
                            validator = ReferenceValidator()
                            if MULTI_SOURCE:
                                st.info("🔍 使用多源验证（ArXiv + Crossref + OpenReview + Scholar）")
                            else:
                                st.info("🔍 使用单源验证（ArXiv）")
                        except Exception as e:
                            st.warning(f"⚠️ 多源验证器初始化失败，使用默认验证器: {e}")
                            from ref_checker.validator import ReferenceValidator
                            validator = ReferenceValidator()
                        
                        results = validator.validate_batch(entries)
                        
                        st.session_state.validation_results = results
                        st.session_state.selected_entry_idx = None
                        
                        os.unlink(tmp_file_path)
                        
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ 验证过程中出错: {str(e)}")
                    import traceback
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())
                    if 'tmp_file_path' in locals():
                        os.unlink(tmp_file_path)

# 文本输入标签页
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
                    parser = BibTeXParser()
                    entries = parser.parse_string(bibtex_text)
                    
                    if not entries:
                        st.error("❌ 未找到任何参考文献条目")
                    else:
                        st.info(f"📚 找到 {len(entries)} 条参考文献，开始验证...")
                        
                        # 使用多源验证器（如果可用）
                        try:
                            validator = ReferenceValidator()
                            if MULTI_SOURCE:
                                st.info("🔍 使用多源验证（ArXiv + Crossref + OpenReview + Scholar）")
                            else:
                                st.info("🔍 使用单源验证（ArXiv）")
                        except Exception as e:
                            st.warning(f"⚠️ 多源验证器初始化失败，使用默认验证器: {e}")
                            from ref_checker.validator import ReferenceValidator
                            validator = ReferenceValidator()
                        
                        results = validator.validate_batch(entries)
                        
                        st.session_state.validation_results = results
                        st.session_state.selected_entry_idx = None
                        
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ 验证过程中出错: {str(e)}")
                    import traceback
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())

# 显示结果
if st.session_state.validation_results:
    display_results(st.session_state.validation_results)
    
    # 报告下载
    st.markdown("---")
    st.subheader("📄 生成报告")
    report_generator = MarkdownReportGenerator()
    report_content = report_generator.generate_report(st.session_state.validation_results)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 下载 Markdown 报告",
            data=report_content,
            file_name="references_report.md",
            mime="text/markdown",
            use_container_width=True
        )
    with col2:
        if st.button("🔄 重新验证", use_container_width=True):
            st.session_state.validation_results = None
            st.session_state.selected_entry_idx = None
            st.rerun()

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 1rem;'>
    <p style='margin: 0;'>LLM参考文献幻觉检测工具 v0.2.0 (Enhanced) | 
    <a href="https://github.com/JijiKing-Sam/LLM-Ref-Check" target="_blank" style='color: #3b82f6; text-decoration: none;'>GitHub</a></p>
</div>
""", unsafe_allow_html=True)

