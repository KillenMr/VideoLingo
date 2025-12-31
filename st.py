import streamlit as st
import streamlit as st
import os, sys, time
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
            2. {t("Sentence segmentation using NLP and LLM")}<br>
            3. {t("Summarization and multi-step translation")}<br>
            4. {t("Cutting and aligning long subtitles")}<br>
            5. {t("Generating timeline and subtitles")}<br>
            6. {t("Merging subtitles into the video")}
        """, unsafe_allow_html=True)



    # Step 1: ASR
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
                
                st.divider()
                st.write("📤 Upload modified 'cleaned_chunks.xlsx'")
                uploaded_asr = st.file_uploader("Select .xlsx file", type="xlsx", key="asr_uploader")
                if uploaded_asr is not None:
                    try:
                        new_df = pd.read_excel(uploaded_asr)
                        # Basic validation: check if 'text' column exists
                        if 'text' not in new_df.columns:
                            st.error("❌ Invalid file format: 'text' column is missing!")
                        else:
                            if st.button("💾 Overwrite with Uploaded File"):
                                new_df.to_excel(_2_CLEANED_CHUNKS, index=False)
                                st.toast("✅ ASR results overwritten successfully!")
                                st.rerun() # Rerun to refresh the editor view
                    except Exception as e:
                        st.error(f"Error reading uploaded file: {e}")

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
        
        # Step 2: NLP Split
        if not os.path.exists(_3_1_SPLIT_BY_NLP):
            if st.button(t("Step 2: Start NLP Sentence Split"), key="step2_btn"):
                with st.spinner(t("Splitting long sentences...")):  
                    _3_1_split_nlp.split_by_spacy()
                st.rerun()
        else:
            st.success(t("Step 2: NLP Sentence Split Complete"))
            col1, col2 = st.columns([1, 1])
            with col1:
                with open(_3_1_SPLIT_BY_NLP, 'rb') as f:
                    st.download_button(label=t("Download NLP Split Results"), data=f, file_name="split_by_nlp.txt", mime="text/plain")
            with col2:
                 if st.button(t("Rerun Step 2"), key="rerun_step2"):
                    # Cascade delete all subsequent files
                    files_to_delete = [_3_1_SPLIT_BY_NLP, _3_2_SPLIT_BY_MEANING, _4_1_TERMINOLOGY, _4_2_TRANSLATION, _5_SPLIT_SUB, _5_REMERGED, SUB_VIDEO]
                    for file in files_to_delete:
                        if os.path.exists(file):
                            os.remove(file)
                    with st.spinner(t("Splitting long sentences...")):  
                        _3_1_split_nlp.split_by_spacy()
                    st.rerun()
            
            # Step 3: LLM Split
            if not os.path.exists(_3_2_SPLIT_BY_MEANING):
                if st.button(t("Step 3: Start LLM Semantic Split"), key="step3_btn"):
                    with st.spinner(t("Splitting sentences by meaning...")):
                        _3_2_split_meaning.split_sentences_by_meaning()
                    st.rerun()
            else:
                st.success(t("Step 3: LLM Semantic Split Complete"))
                col1, col2 = st.columns([1, 1])
                with col1:
                    with open(_3_2_SPLIT_BY_MEANING, 'rb') as f:
                        st.download_button(label=t("Download LLM Split Results"), data=f, file_name="split_by_meaning.txt", mime="text/plain")
                with col2:
                     if st.button(t("Rerun Step 3"), key="rerun_step3"):
                        # Cascade delete all subsequent files
                        files_to_delete = [_3_2_SPLIT_BY_MEANING, _4_1_TERMINOLOGY, _4_2_TRANSLATION, _5_SPLIT_SUB, _5_REMERGED, SUB_VIDEO]
                        for file in files_to_delete:
                            if os.path.exists(file):
                                os.remove(file)
                        with st.spinner(t("Splitting sentences by meaning...")):
                            _3_2_split_meaning.split_sentences_by_meaning()
                        st.rerun()

                # Step 4: Translate
                if not os.path.exists(_4_2_TRANSLATION):
                    if st.button(t("Step 4: Start Translation"), key="step4_btn"):
                        with st.spinner(t("Summarizing and translating...")):
                            _4_1_summarize.get_summary()
                            _4_2_translate.translate_all()
                        st.rerun()
                else:
                    st.success(t("Step 4: Translation Complete"))
                    
                    # 📝 Edit / Upload Subtitles (Force Align Workflow)
                    with st.expander("📝 Edit / Upload Subtitles", expanded=False):
                        st.write("You can edit the translation locally or upload a custom subtitle file for alignment.")
                        col_dl, col_ul = st.columns([1, 1])
                        
                        with col_dl:
                            with open(_4_2_TRANSLATION, 'rb') as f:
                                st.download_button(label=t("Download Translation Results"), data=f, file_name="translation_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                        
                        st.divider()
                        
                        uploaded_trans = st.file_uploader("Upload custom subtitles (.xlsx)", type="xlsx", help="Must contain columns: 'Source', 'Translation'")
                        if uploaded_trans:
                            try:
                                new_df = pd.read_excel(uploaded_trans)
                                if 'Source' not in new_df.columns or 'Translation' not in new_df.columns:
                                    st.error("❌ Invalid file format: Must contain 'Source' and 'Translation' columns!")
                                else:
                                    if st.button("💾 Overwrite with Uploaded File", key="overwrite_trans"):
                                        new_df.to_excel(_4_2_TRANSLATION, index=False)
                                        st.toast("✅ Translation results overwritten successfully!")
                                        time.sleep(1) # Wait a bit for toast
                                        st.rerun()
                            except Exception as e:
                                st.error(f"Error reading uploaded file: {e}")

                    # Step 5: Gen Subtitles
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

def process_text():
    # Deprecated monolithic function, kept potentially for CLI or other calls if needed, 
    # but the UI now uses step-by-step logic inside text_processing_section.
    pass

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

