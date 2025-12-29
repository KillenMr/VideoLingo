import streamlit as st
import os, sys
from core.st_utils.imports_and_utils import *
from core.st_utils.segmentation_preview import show_segmentation_preview
from core import *
from core.utils.models import _2_CLEANED_CHUNKS, _3_1_SPLIT_BY_NLP, _3_2_SPLIT_BY_MEANING

# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="docs/logo.svg")

SUB_VIDEO = "output/output_sub.mp4"
DUB_VIDEO = "output/output_dub.mp4"

def text_processing_section():
    st.header(t("b. Translate and Generate Subtitles"))
    
    # ===== Step 1: 转录和分段 =====
    with st.container(border=True):
        st.subheader("📝 " + t("Step 1: Transcription and Segmentation"))
        st.markdown(f"""
        <p style='font-size: 18px;'>
            1. {t("WhisperX word-level transcription")}<br>
            2. {t("Sentence segmentation using NLP and LLM")}
        </p>
        """, unsafe_allow_html=True)
        
        # 检查是否已完成步骤 1
        if not os.path.exists(_3_2_SPLIT_BY_MEANING):
            # 未完成 → 显示开始按钮
            if st.button(t("Start Transcription and Segmentation"), key="step_1_button", type="primary", use_container_width=True):
                process_transcription_and_segmentation()
                st.rerun()
        else:
            # 已完成 → 显示预览
            st.success("✅ " + t("Step 1 Complete!"))
            
            # 显示分段预览
            show_segmentation_preview()
            
            # 操作按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ " + t("Continue to Translation"), key="continue_to_step2", type="primary", use_container_width=True):
                    st.session_state.segmentation_approved = True
                    st.rerun()
            with col2:
                if st.button("🔄 " + t("Redo Segmentation"), key="redo_step1", use_container_width=True):
                    cleanup_step_1()
                    st.rerun()
    
    # ===== Step 2: 翻译和字幕生成 =====
    # 只有在用户确认步骤 1 后才显示
    if st.session_state.get('segmentation_approved', False) or os.path.exists(SUB_VIDEO):
        with st.container(border=True):
            st.subheader("🌐 " + t("Step 2: Translation and Subtitle Generation"))
            st.markdown(f"""
            <p style='font-size: 18px;'>
                1. {t("Summarization and multi-step translation")}<br>
                2. {t("Cutting and aligning long subtitles")}<br>
                3. {t("Generating timeline and subtitles")}<br>
                4. {t("Merging subtitles into the video")}
            </p>
            """, unsafe_allow_html=True)
            
            if not os.path.exists(SUB_VIDEO):
                # 未完成 → 显示开始按钮
                if st.button(t("Start Translation and Subtitle Generation"), key="step_2_button", type="primary", use_container_width=True):
                    process_translation_and_subtitle_generation()
                    st.rerun()
            else:
                # 已完成 → 显示结果
                st.success("✅ " + t("Step 2 Complete!"))
                
                if load_key("burn_subtitles"):
                    st.video(SUB_VIDEO)
                
                download_subtitle_zip_button(text=t("Download All Srt Files"))
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 " + t("Redo Translation"), key="redo_step2", use_container_width=True):
                        cleanup_step_2()
                        st.rerun()
                with col2:
                    if st.button("📁 " + t("Archive to 'history'"), key="cleanup_all", use_container_width=True):
                        cleanup()
                        st.rerun()


def process_transcription_and_segmentation():
    """执行步骤 1: 转录和分段"""
    with st.spinner(t("Using Whisper for transcription...")):
        _2_asr.transcribe()
    with st.spinner(t("Splitting long sentences...")):
        _3_1_split_nlp.split_by_spacy()
        _3_2_split_meaning.split_sentences_by_meaning()
    st.success(t("Transcription and segmentation complete! 🎉"))


def process_translation_and_subtitle_generation():
    """执行步骤 2: 翻译和字幕生成"""
    with st.spinner(t("Summarizing and translating...")):
        _4_1_summarize.get_summary()
        if load_key("pause_before_translate"):
            input(t("⚠️ PAUSE_BEFORE_TRANSLATE. Go to `output/log/terminology.json` to edit terminology. Then press ENTER to continue..."))
        _4_2_translate.translate_all()
    with st.spinner(t("Processing and aligning subtitles...")):
        _5_split_sub.split_for_sub_main()
        _6_gen_sub.align_timestamp_main()
    with st.spinner(t("Merging subtitles to video...")):
        _7_sub_into_vid.merge_subtitles_to_video()
    
    st.success(t("Translation and subtitle generation complete! 🎉"))
    st.balloons()


def cleanup_step_1():
    """清理步骤 1 的输出文件"""
    files_to_remove = [
        _2_CLEANED_CHUNKS,
        _3_1_SPLIT_BY_NLP,
        _3_2_SPLIT_BY_MEANING
    ]
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
    
    # 清除会话状态
    if 'segmentation_approved' in st.session_state:
        del st.session_state['segmentation_approved']
    
    st.success(t("Step 1 files cleared. Ready to redo."))


def cleanup_step_2():
    """清理步骤 2 的输出文件（保留步骤 1）"""
    from core.utils.models import _4_1_TERMINOLOGY, _4_2_TRANSLATION, _5_SPLIT_SUB, _5_REMERGED
    
    files_to_remove = [
        _4_1_TERMINOLOGY,
        _4_2_TRANSLATION,
        _5_SPLIT_SUB,
        _5_REMERGED,
        SUB_VIDEO,
        "output/src.srt",
        "output/trans.srt",
        "output/src_trans.srt",
        "output/trans_src.srt"
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
    
    st.success(t("Step 2 files cleared. Ready to redo translation."))

def audio_processing_section():
    st.header(t("c. Dubbing"))
    with st.container(border=True):
        st.markdown(f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("Generate audio tasks and chunks")}<br>
            2. {t("Extract reference audio")}<br>
            3. {t("Generate and merge audio files")}<br>
            4. {t("Merge final audio into video")}
        """, unsafe_allow_html=True)
        if not os.path.exists(DUB_VIDEO):
            if st.button(t("Start Audio Processing"), key="audio_processing_button"):
                process_audio()
                st.rerun()
        else:
            st.success(t("Audio processing is complete! You can check the audio files in the `output` folder."))
            if load_key("burn_subtitles"):
                st.video(DUB_VIDEO) 
            if st.button(t("Delete dubbing files"), key="delete_dubbing_files"):
                delete_dubbing_files()
                st.rerun()
            if st.button(t("Archive to 'history'"), key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()

def process_audio():
    with st.spinner(t("Generate audio tasks")): 
        _8_1_audio_task.gen_audio_task_main()
        _8_2_dub_chunks.gen_dub_chunks()
    with st.spinner(t("Extract refer audio")):
        _9_refer_audio.extract_refer_audio_main()
    with st.spinner(t("Generate all audio")):
        _10_gen_audio.gen_audio()
    with st.spinner(t("Merge full audio")):
        _11_merge_audio.merge_full_audio()
    with st.spinner(t("Merge dubbing to the video")):
        _12_dub_to_vid.merge_video_audio()
    
    st.success(t("Audio processing complete! 🎇"))
    st.balloons()

def main():
    logo_col, _ = st.columns([1,1])
    with logo_col:
        st.image("docs/logo.png", use_column_width=True)
    st.markdown(button_style, unsafe_allow_html=True)
    welcome_text = t("Hello, welcome to VideoLingo. If you encounter any issues, feel free to get instant answers with our Free QA Agent <a href=\"https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh\" target=\"_blank\">here</a>! You can also try out our SaaS website at <a href=\"https://videolingo.io\" target=\"_blank\">videolingo.io</a> for free!")
    st.markdown(f"<p style='font-size: 20px; color: #808080;'>{welcome_text}</p>", unsafe_allow_html=True)
    # add settings
    with st.sidebar:
        page_setting()
        st.markdown(give_star_button, unsafe_allow_html=True)
    download_video_section()
    text_processing_section()
    audio_processing_section()

if __name__ == "__main__":
    main()
