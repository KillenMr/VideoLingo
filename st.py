import streamlit as st
import os, sys, time
from io import BytesIO
import pandas as pd
from core.st_utils.imports_and_utils import *
from core import *
from core.utils.models import _2_CLEANED_CHUNKS, _3_1_SPLIT_BY_NLP, _3_2_SPLIT_BY_MEANING, _4_2_TRANSLATION, _5_SPLIT_SUB, _4_1_TERMINOLOGY, _5_REMERGED

# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="docs/logo.svg")

SUB_VIDEO = "output/output_sub.mp4"
DUB_VIDEO = "output/output_dub.mp4"

def text_processing_section():
    st.header(t("b. Translate and Generate Subtitles"))
    with st.container(border=True):
        st.markdown(f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("WhisperX word-level transcription")}<br>
            2. {t("Upload custom subtitles")}<br>
            3. {t("Generating timeline and subtitles")}<br>
            4. {t("Merging subtitles into the video")}
        """, unsafe_allow_html=True)

    # Step 1: ASR
    if not os.path.exists(_2_CLEANED_CHUNKS):
        if st.button(t("Step 1: Start Whisper Transcription"), key="step1_btn"):
            with st.spinner(t("Using Whisper for transcription...")):
                _2_asr.transcribe()
            st.rerun()
    else:
        st.success(t("Step 1: Whisper Transcription Complete"))
        
        # 📝 ASR Data Editor
        if os.path.exists(_2_CLEANED_CHUNKS):
            with st.expander("📝 Edit ASR Results", expanded=False):
                try:
                    df = pd.read_excel(_2_CLEANED_CHUNKS)
                    # Use st.data_editor to allow editing
                    edited_df = st.data_editor(df, num_rows="dynamic", key="asr_editor")
                    if st.button("💾 Save ASR Changes"):
                        edited_df.to_excel(_2_CLEANED_CHUNKS, index=False)
                        st.toast("✅ ASR results updated successfully!")
                except Exception as e:
                    st.error(f"Error reading/saving Excel: {e}")
                
        col1, col2 = st.columns([1, 1])
        with col1:
            with open(_2_CLEANED_CHUNKS, 'rb') as f:
                st.download_button(label=t("Download ASR Results"), data=f, file_name="cleaned_chunks.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col2:
            if st.button(t("Rerun Step 1"), key="rerun_step1"):
                # Cascade delete all subsequent files
                files_to_delete = [_2_CLEANED_CHUNKS, _3_1_SPLIT_BY_NLP, _3_2_SPLIT_BY_MEANING, _4_1_TERMINOLOGY, _4_2_TRANSLATION, _5_SPLIT_SUB, _5_REMERGED, SUB_VIDEO]
                for file in files_to_delete:
                    if os.path.exists(file):
                        os.remove(file)
                with st.spinner(t("Using Whisper for transcription...")):
                    _2_asr.transcribe()
                st.rerun()
        
        # 🚀 Upload Subtitles directly
        st.divider()
        with st.expander("🚀 Upload Subtitles for Force Alignment", expanded=True):
            st.write(t("Upload a custom subtitle file (.xlsx) with 'Source' and 'Translation' columns to skip NLP steps and directly align timestamps."))
            
            # Template Download Button
            df_template = pd.DataFrame({'Source': ['こんにちは世界', 'これはテストです'], 'Translation': ['你好世界', '这是一个测试'], "timestamp": ["", ""], "duration": ["", ""]})
            buffer = BytesIO()
            df_template.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                label="⬇️ Download Subtitle Template",
                data=buffer,
                file_name="subtitle_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            uploaded_trans = st.file_uploader("Upload custom subtitles", type="xlsx", key="force_align_uploader")
            if uploaded_trans:
                try:
                    new_df = pd.read_excel(uploaded_trans)
                    if 'Source' not in new_df.columns or 'Translation' not in new_df.columns:
                        st.error("❌ Invalid file format: Must contain 'Source' and 'Translation' columns!")
                    else:
                        if st.button("💾 Save & Update", key="force_align_save"):
                            new_df.to_excel(_4_2_TRANSLATION, index=False)
                            st.toast("✅ Subtitles processed! Ready for Step 3.")
                            time.sleep(1)
                            st.rerun()
                except Exception as e:
                    st.error(f"Error reading uploaded file: {e}")

        # Step 5: Gen Subtitles (Shown if _4_2_TRANSLATION exists)
        if os.path.exists(_4_2_TRANSLATION):
            st.divider()
            if not os.path.exists(SUB_VIDEO):
                if st.button(t("Step 5: Generate Subtitles & Video"), key="step5_btn"):
                    with st.spinner(t("Processing and aligning subtitles...")): 
                        _5_split_sub.split_for_sub_main()
                        _6_gen_sub.align_timestamp_main()
                    with st.spinner(t("Merging subtitles to video...")):
                        _7_sub_into_vid.merge_subtitles_to_video()
                    st.rerun()
            else:
                st.success(t("Step 5: Subtitle Generation Complete"))
                if load_key("burn_subtitles"):
                    st.video(SUB_VIDEO)
                download_subtitle_zip_button(text=t("Download All Srt Files"))
                
                if st.button(t("Archive to 'history'"), key="cleanup_in_text_processing"):
                    cleanup()
                    st.rerun()
                return True

@st.dialog("📖 字幕时间轴校准使用操作说明", width="large")
def view_manual():
    import re
    import base64
    try:
        with open("docs/pages/docs/manual.zh-CN.md", "r", encoding="utf-8") as f:
            md_content = f.read()
            
        # Split by markdown image syntax: ![alt](path)
        parts = re.split(r'!\[.*?\]\((.*?)\)', md_content)
        
        for i, part in enumerate(parts):
            if i % 2 == 0:
                st.markdown(part)
            else:
                # Image path adjustment
                img_path = part.replace("./public/images/", "docs/pages/docs/public/images/")
                if os.path.exists(img_path):
                    with open(img_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode()
                    st.markdown(
                        f'<img src="data:image/png;base64,{encoded_string}" style="border: 2px solid #e0e0e0; border-radius: 10px; width: 100%; margin: 10px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">',
                        unsafe_allow_html=True
                    )
    except Exception as e:
        st.error(f"Could not load manual: {e}")

def main():
    logo_col, help_col = st.columns([1, 1], vertical_alignment="center")
    with logo_col:
        st.image("docs/logo.png", use_column_width=True)
    with help_col:
        if st.button("📖 字幕时间轴校准使用操作说明", key="manual_btn", help="点击查看详细操作手册"):
            view_manual()
    st.markdown(button_style, unsafe_allow_html=True)
    welcome_text = t("Hello, welcome to VideoLingo. If you encounter any issues, feel free to get instant answers with our Free QA Agent <a href=\"https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh\" target=\"_blank\">here</a>! You can also try out our SaaS website at <a href=\"https://videolingo.io\" target=\"_blank\">videolingo.io</a> for free!")
    st.markdown(f"<p style='font-size: 20px; color: #808080;'>{welcome_text}</p>", unsafe_allow_html=True)
    # add settings
    with st.sidebar:
        page_setting()
        st.markdown(give_star_button, unsafe_allow_html=True)
    download_video_section()
    text_processing_section()

if __name__ == "__main__":
    main()

