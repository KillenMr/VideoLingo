import pandas as pd
import os
import re
from rich.panel import Panel
from rich.console import Console
import autocorrect_py as autocorrect
from core.utils import *
from core.utils.models import *
console = Console()

SUBTITLE_OUTPUT_CONFIGS = [ 
    ('src.srt', ['Source']),
    ('trans.srt', ['Translation']),
    ('src_trans.srt', ['Source', 'Translation']),
    ('trans_src.srt', ['Translation', 'Source'])
]

AUDIO_SUBTITLE_OUTPUT_CONFIGS = [
    ('src_subs_for_audio.srt', ['Source']),
    ('trans_subs_for_audio.srt', ['Translation'])
]

def convert_to_srt_format(start_time, end_time):
    """Convert time (in seconds) to the format: hours:minutes:seconds,milliseconds"""
    def seconds_to_hmsm(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int(seconds * 1000) % 1000
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

    start_srt = seconds_to_hmsm(start_time)
    end_srt = seconds_to_hmsm(end_time)
    return f"{start_srt} --> {end_srt}"

def remove_punctuation(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def show_difference(str1, str2):
    """Show the difference positions between two strings"""
    min_len = min(len(str1), len(str2))
    diff_positions = []
    
    for i in range(min_len):
        if str1[i] != str2[i]:
            diff_positions.append(i)
    
    if len(str1) != len(str2):
        diff_positions.extend(range(min_len, max(len(str1), len(str2))))
    
    print("Difference positions:")
    print(f"Expected sentence: {str1}")
    print(f"Actual match: {str2}")
    print("Position markers: " + "".join("^" if i in diff_positions else " " for i in range(max(len(str1), len(str2)))))
    print(f"Difference indices: {diff_positions}")

from difflib import SequenceMatcher

def get_sentence_timestamps(df_words, df_sentences):
    time_stamp_list = []
    
    # Build complete string and position mapping
    full_words_str = ''
    position_to_word_idx = {}
    
    for idx, word in enumerate(df_words['text']):
        clean_word = remove_punctuation(word.lower())
        start_pos = len(full_words_str)
        full_words_str += clean_word
        for pos in range(start_pos, len(full_words_str)):
            position_to_word_idx[pos] = idx
    
    current_pos = 0
    total_len = len(full_words_str)
    
    for idx, sentence in df_sentences['Source'].items():
        clean_sentence = remove_punctuation(str(sentence).lower()).replace(" ", "")
        sentence_len = len(clean_sentence)
        if sentence_len == 0:
            # Handle empty source lines gracefully
            start_time = time_stamp_list[-1][1] if time_stamp_list else 0.0
            time_stamp_list.append((start_time, start_time))
            continue

        best_match_score = 0
        best_match_start = -1
        best_match_end = -1
        
        # Fuzzy Search Window: Search ahead up to 2x sentence length or 100 chars min
        search_window = max(200, sentence_len * 3) 
        
        # Optimize: sliding window with step 1 may be slow, can optimize step if needed
        # For strict-ish fuzzy match
        for i in range(current_pos, min(current_pos + search_window, total_len)):
            # Quick check length
            # Trying to match a substring of length roughly equal to sentence_len
            # Allow variance in length
            for length_variance in range(-5, 6): # +/- 5 chars length
                check_len = sentence_len + length_variance
                if params := (i, i + check_len, total_len):
                     if params[1] > params[2]: break
                
                candidate = full_words_str[i : i + check_len]
                score = SequenceMatcher(None, clean_sentence, candidate).ratio()
                
                if score > best_match_score:
                    best_match_score = score
                    best_match_start = i
                    best_match_end = i + check_len

        # Threshold for accepting a match
        if best_match_score > 0.6: # 60% similarity
            start_word_idx = position_to_word_idx[best_match_start]
            # carefully handle end index mapping
            # define end_pos as the last character index included in the match
            end_pos_search = best_match_end - 1
            if end_pos_search not in position_to_word_idx:
                 end_pos_search = max(k for k in position_to_word_idx if k < best_match_end)
            
            end_word_idx = position_to_word_idx[end_pos_search]

            start_t = float(df_words['start'][start_word_idx])
            end_t = float(df_words['end'][end_word_idx])
            
            time_stamp_list.append((start_t, end_t))
            current_pos = best_match_end 
            # console.print(f"[green]Match: {best_match_score:.2f} | {sentence[:20]}...[/green]")
        else:
            # INTERPOLATION FALLBACK
            console.print(f"[yellow]⚠️ Fuzzy match failed (score={best_match_score:.2f}) for: {sentence[:30]}... Using interpolation.[/yellow]")
            
            prev_end = time_stamp_list[-1][1] if time_stamp_list else 0.0
            
            # Estimate duration based on char length (rough speed: 15 chars/sec)
            estimated_duration = max(1.0, len(clean_sentence) / 15.0)
            new_end = prev_end + estimated_duration
            
            # Check if we are exceeding next known word (if any left) -- tricky without lookahead
            # Simple fallback: use estimated times.
            time_stamp_list.append((prev_end, new_end))
            # Do NOT advance current_pos if we didn't find a match in the audio stream
            # This allows the NEXT sentence to potentialy match the current_pos

    
    return time_stamp_list

def align_timestamp(df_text, df_translate, subtitle_output_configs: list, output_dir: str, for_display: bool = True):
    """Align timestamps and add a new timestamp column to df_translate"""
    df_trans_time = df_translate.copy()

    # Assign an ID to each word in df_text['text'] and create a new DataFrame
    words = df_text['text'].str.split(expand=True).stack().reset_index(level=1, drop=True).reset_index()
    words.columns = ['id', 'word']
    words['id'] = words['id'].astype(int)

    # Process timestamps ⏰
    time_stamp_list = get_sentence_timestamps(df_text, df_translate)
    df_trans_time['timestamp'] = time_stamp_list
    df_trans_time['duration'] = df_trans_time['timestamp'].apply(lambda x: x[1] - x[0])

    # Remove gaps 🕳️
    for i in range(len(df_trans_time)-1):
        delta_time = df_trans_time.loc[i+1, 'timestamp'][0] - df_trans_time.loc[i, 'timestamp'][1]
        if 0 < delta_time < 1:
            df_trans_time.at[i, 'timestamp'] = (df_trans_time.loc[i, 'timestamp'][0], df_trans_time.loc[i+1, 'timestamp'][0])

    # Convert start and end timestamps to SRT format
    df_trans_time['timestamp'] = df_trans_time['timestamp'].apply(lambda x: convert_to_srt_format(x[0], x[1]))

    # Polish subtitles: replace punctuation in Translation if for_display
    if for_display:
        df_trans_time['Translation'] = df_trans_time['Translation'].apply(lambda x: re.sub(r'[，。]', ' ', x).strip())

    # Output subtitles 📜
    def generate_subtitle_string(df, columns):
        return ''.join([f"{i+1}\n{row['timestamp']}\n{row[columns[0]].strip()}\n{row[columns[1]].strip() if len(columns) > 1 else ''}\n\n" for i, row in df.iterrows()]).strip()

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        for filename, columns in subtitle_output_configs:
            subtitle_str = generate_subtitle_string(df_trans_time, columns)
            with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
                f.write(subtitle_str)
    
    return df_trans_time

# ✨ Beautify the translation
def clean_translation(x):
    if pd.isna(x):
        return ''
    cleaned = str(x).strip('。').strip('，')
    return autocorrect.format(cleaned)

def align_timestamp_main():
    df_text = pd.read_excel(_2_CLEANED_CHUNKS)
    df_text['text'] = df_text['text'].str.strip('"').str.strip()
    df_translate = pd.read_excel(_5_SPLIT_SUB)
    df_translate['Translation'] = df_translate['Translation'].apply(clean_translation)
    
    align_timestamp(df_text, df_translate, SUBTITLE_OUTPUT_CONFIGS, _OUTPUT_DIR)
    console.print(Panel("[bold green]🎉📝 Subtitles generation completed! Please check in the `output` folder 👀[/bold green]"))

    # for audio
    df_translate_for_audio = pd.read_excel(_5_REMERGED) # use remerged file to avoid unmatched lines when dubbing
    df_translate_for_audio['Translation'] = df_translate_for_audio['Translation'].apply(clean_translation)
    
    align_timestamp(df_text, df_translate_for_audio, AUDIO_SUBTITLE_OUTPUT_CONFIGS, _AUDIO_DIR)
    console.print(Panel(f"[bold green]🎉📝 Audio subtitles generation completed! Please check in the `{_AUDIO_DIR}` folder 👀[/bold green]"))
    

if __name__ == '__main__':
    align_timestamp_main()
