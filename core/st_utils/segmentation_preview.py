"""分段预览工具模块"""
import streamlit as st
import pandas as pd
import os
from core.utils.models import _3_2_SPLIT_BY_MEANING
from translations.translations import translate as t


def show_segmentation_preview():
    """显示分段预览界面"""
    st.markdown("### 📊 " + t("Segmentation Preview"))
    
    # 读取分段结果
    try:
        with open(_3_2_SPLIT_BY_MEANING, 'r', encoding='utf-8') as f:
            segments = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        st.error(t("Segmentation file not found. Please run transcription first."))
        return
    
    if not segments:
        st.warning(t("No segments found."))
        return
    
    # 计算统计信息
    word_counts = [len(s.split()) for s in segments]
    avg_length = sum(word_counts) / len(word_counts)
    max_length = max(word_counts)
    min_length = min(word_counts)
    
    # 显示统计信息
    st.markdown(f"**{t('Statistics')}:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(t("Total Segments"), len(segments))
    with col2:
        st.metric(t("Avg Length"), f"{avg_length:.1f} " + t("words"))
    with col3:
        st.metric(t("Max Length"), f"{max_length} " + t("words"))
    with col4:
        st.metric(t("Min Length"), f"{min_length} " + t("words"))
    
    # 显示前 10 条预览
    st.markdown(f"**{t('Preview (first 10 segments)')}:**")
    preview_count = min(10, len(segments))
    preview_df = pd.DataFrame({
        '#': range(1, preview_count + 1),
        t('Words'): word_counts[:preview_count],
        t('Segment'): segments[:preview_count]
    })
    st.dataframe(preview_df, use_container_width=True, hide_index=True)
    
    # 完整列表（可折叠）
    if len(segments) > 10:
        with st.expander(t("Show All {count} Segments").format(count=len(segments))):
            full_df = pd.DataFrame({
                '#': range(1, len(segments) + 1),
                t('Words'): word_counts,
                t('Segment'): segments
            })
            st.dataframe(full_df, use_container_width=True, hide_index=True, height=400)
    
    # 下载按钮
    st.download_button(
        label="📄 " + t("Download Segmentation Results"),
        data='\n'.join(segments),
        file_name='segmentation_results.txt',
        mime='text/plain',
        use_container_width=True
    )
