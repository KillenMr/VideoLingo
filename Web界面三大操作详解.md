# VideoLingo Web 界面操作详解

## 📋 界面概览

VideoLingo 的 Streamlit Web 界面提供了**三个主要操作区域**，按顺序依次执行：

```
┌─────────────────────────────────────────────────────────┐
│  🎬 a. Download or Upload Video                        │
│  ← 第一步：获取视频                                    │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  📝 b. Translate and Generate Subtitles                │
│  ← 第二步：字幕翻译生成                                │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  🎙️ c. Dubbing                                         │
│  ← 第三步：配音（可选）                                │
└─────────────────────────────────────────────────────────┘
```

---

## 🎬 操作一：上传/下载视频

> **文件**: `core/st_utils/download_video_section.py`  
> **函数**: `download_video_section()`

### 功能概述

这一步提供**两种方式**获取待处理的视频：

1. **下载 YouTube 视频**
2. **上传本地视频/音频文件**

### 界面元素

#### 场景 1: 没有视频时

```
┌──────────────────────────────────────────────────┐
│ a. Download or Upload Video                     │
├──────────────────────────────────────────────────┤
│                                                  │
│ Enter YouTube link: [___________________]  [1080p▼] │
│                                                  │
│ [Download Video]                                 │
│                                                  │
│ ─────────────── Or ───────────────              │
│                                                  │
│ Or upload video: [Choose File]                  │
│                                                  │
└──────────────────────────────────────────────────┘
```

#### 场景 2: 已有视频时

```
┌──────────────────────────────────────────────────┐
│ a. Download or Upload Video                     │
├──────────────────────────────────────────────────┤
│                                                  │
│ ┌────────────────────────────────────────────┐  │
│ │                                            │  │
│ │       🎥 Video Preview                     │  │
│ │                                            │  │
│ └────────────────────────────────────────────┘  │
│                                                  │
│ [Delete and Reselect]                            │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 实现逻辑

```python
def download_video_section():
    st.header(t("a. Download or Upload Video"))
    with st.container(border=True):
        try:
            # 尝试查找已存在的视频文件
            video_file = find_video_files()
            st.video(video_file)  # 显示视频预览

            # 提供删除按钮
            if st.button(t("Delete and Reselect"), key="delete_video_button"):
                os.remove(video_file)  # 删除视频
                if os.path.exists(OUTPUT_DIR):
                    shutil.rmtree(OUTPUT_DIR)  # 清空输出目录
                st.rerun()  # 刷新页面
            return True

        except:
            # 没有视频时，显示下载/上传界面

            # 1️⃣ YouTube 下载
            col1, col2 = st.columns([3, 1])
            with col1:
                url = st.text_input(t("Enter YouTube link:"))
            with col2:
                res_dict = {"360p": "360", "1080p": "1080", "Best": "best"}
                res_display = st.selectbox(t("Resolution"), options=list(res_dict.keys()))
                res = res_dict[res_display]

            if st.button(t("Download Video")):
                if url:
                    with st.spinner("Downloading video..."):
                        download_video_ytdlp(url, resolution=res)
                    st.rerun()

            # 2️⃣ 本地上传
            uploaded_file = st.file_uploader(
                t("Or upload video"),
                type=load_key("allowed_video_formats") + load_key("allowed_audio_formats")
            )

            if uploaded_file:
                # 清空旧数据
                if os.path.exists(OUTPUT_DIR):
                    shutil.rmtree(OUTPUT_DIR)
                os.makedirs(OUTPUT_DIR, exist_ok=True)

                # 清理文件名
                raw_name = uploaded_file.name.replace(' ', '_')
                name, ext = os.path.splitext(raw_name)
                clean_name = re.sub(r'[^\w\-_\.]', '', name) + ext.lower()

                # 保存文件
                with open(os.path.join(OUTPUT_DIR, clean_name), "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # 如果是音频文件，转换为视频
                if ext.lower() in load_key("allowed_audio_formats"):
                    convert_audio_to_video(os.path.join(OUTPUT_DIR, clean_name))

                st.rerun()
```

### 支持的格式

#### 视频格式

```yaml
allowed_video_formats:
  - "mp4"
  - "mov"
  - "avi"
  - "mkv"
  - "flv"
  - "wmv"
  - "webm"
```

#### 音频格式

```yaml
allowed_audio_formats:
  - "wav"
  - "mp3"
  - "flac"
  - "m4a"
```

### 特殊处理：音频转视频

如果上传的是音频文件，会自动转换为**黑屏视频**：

```python
def convert_audio_to_video(audio_file: str) -> str:
    """将音频转换为黑屏视频"""
    output_video = os.path.join(OUTPUT_DIR, 'black_screen.mp4')

    # FFmpeg 命令：创建黑色背景 + 添加音频
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', 'color=c=black:s=640x360',  # 黑色背景
        '-i', audio_file,  # 音频
        '-shortest',  # 以最短的流为准
        '-c:v', 'libx264',  # H.264 视频编码
        '-c:a', 'aac',  # AAC 音频编码
        '-pix_fmt', 'yuv420p',  # 像素格式
        output_video
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    os.remove(audio_file)  # 删除原音频文件
    return output_video
```

**示例**：

```
上传: podcast.mp3 (纯音频)
      ↓
转换: black_screen.mp4 (黑屏视频 + 音频)
      ↓
删除: podcast.mp3
```

---

## 📝 操作二：字幕翻译生成

> **文件**: `st.py`  
> **函数**: `text_processing_section()` + `process_text()`

### 功能概述

这是 VideoLingo 的**核心功能**，包含 **6 个处理步骤**：

1. WhisperX 词级转录
2. NLP 和 LLM 句子分割
3. 摘要和多步翻译
4. 长字幕切割和对齐
5. 时间戳对齐和字幕生成
6. 字幕烧录到视频

### 界面元素

#### 场景 1: 未处理时

```
┌──────────────────────────────────────────────────┐
│ b. Translate and Generate Subtitles             │
├──────────────────────────────────────────────────┤
│                                                  │
│ This stage includes the following steps:        │
│   1. WhisperX word-level transcription          │
│   2. Sentence segmentation using NLP and LLM    │
│   3. Summarization and multi-step translation   │
│   4. Cutting and aligning long subtitles        │
│   5. Generating timeline and subtitles          │
│   6. Merging subtitles into the video           │
│                                                  │
│ [Start Processing Subtitles]                    │
│                                                  │
└──────────────────────────────────────────────────┘
```

#### 场景 2: 处理完成后

```
┌──────────────────────────────────────────────────┐
│ b. Translate and Generate Subtitles             │
├──────────────────────────────────────────────────┤
│                                                  │
│ ┌────────────────────────────────────────────┐  │
│ │                                            │  │
│ │   🎥 Video with Subtitles Preview          │  │
│ │                                            │  │
│ └────────────────────────────────────────────┘  │
│                                                  │
│ [Download All Srt Files]                        │
│                                                  │
│ [Archive to 'history']                          │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 处理流程

```python
def text_processing_section():
    st.header(t("b. Translate and Generate Subtitles"))
    with st.container(border=True):
        # 显示步骤说明
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

        # 检查是否已完成
        if not os.path.exists(SUB_VIDEO):  # SUB_VIDEO = "output/output_sub.mp4"
            # 未完成，显示处理按钮
            if st.button(t("Start Processing Subtitles")):
                process_text()  # 执行处理
                st.rerun()  # 刷新页面
        else:
            # 已完成，显示结果
            if load_key("burn_subtitles"):
                st.video(SUB_VIDEO)  # 显示带字幕的视频

            # 下载字幕文件
            download_subtitle_zip_button(text=t("Download All Srt Files"))

            # 归档按钮
            if st.button(t("Archive to 'history'")):
                cleanup()  # 清理并归档
                st.rerun()
```

### 核心处理函数

```python
def process_text():
    """执行完整的字幕处理流程"""

    # 步骤 1: ASR 转录 (约 2-5 分钟)
    with st.spinner(t("Using Whisper for transcription...")):
        _2_asr.transcribe()

    # 步骤 2: 句子分割 (约 1-2 分钟)
    with st.spinner(t("Splitting long sentences...")):
        _3_1_split_nlp.split_by_spacy()  # NLP 规则分割
        _3_2_split_meaning.split_sentences_by_meaning()  # LLM 语义分割

    # 步骤 3: 摘要和翻译 (约 3-10 分钟，取决于长度)
    with st.spinner(t("Summarizing and translating...")):
        _4_1_summarize.get_summary()  # 提取摘要和术语

        # 可选：暂停让用户编辑术语表
        if load_key("pause_before_translate"):
            input(t("⚠️ PAUSE_BEFORE_TRANSLATE. Go to `output/log/terminology.json` to edit terminology. Then press ENTER to continue..."))

        _4_2_translate.translate_all()  # 多线程翻译

    # 步骤 4: 字幕切割和对齐 (约 1-2 分钟)
    with st.spinner(t("Processing and aligning subtitles...")):
        _5_split_sub.split_for_sub_main()  # 长度切割
        _6_gen_sub.align_timestamp_main()  # 时间戳对齐

    # 步骤 5: 字幕烧录 (约 30 秒 - 2 分钟)
    with st.spinner(t("Merging subtitles to video...")):
        _7_sub_into_vid.merge_subtitles_to_video()

    # 完成！
    st.success(t("Subtitle processing complete! 🎉"))
    st.balloons()  # 🎈 庆祝动画
```

### 生成的文件

#### 输出目录结构

```
output/
├── output_sub.mp4              ← 带字幕的视频（主要输出）
├── src.srt                     ← 源语言字幕
├── trans.srt                   ← 目标语言字幕
├── src_trans.srt               ← 双语字幕（源+译）
├── trans_src.srt               ← 双语字幕（译+源）
├── log/
│   ├── cleaned_chunks.xlsx     ← 词级时间戳数据
│   ├── _3_1_nlp_processed.txt  ← NLP 分割结果
│   ├── _3_2_meaning_processed.txt ← LLM 分割结果
│   ├── terminology.json        ← 术语表
│   ├── _4_2_translation.xlsx   ← 翻译结果
│   ├── _5_split_sub.xlsx       ← 切割后的字幕
│   └── _5_remerged.xlsx        ← 配音用字幕
└── audio/
    ├── src_subs_for_audio.srt  ← 配音用源语言字幕
    └── trans_subs_for_audio.srt ← 配音用译文字幕
```

### 下载字幕功能

点击 **"Download All Srt Files"** 会下载一个 ZIP 文件：

```python
def download_subtitle_zip_button(text: str):
    """打包所有 .srt 文件为 ZIP"""
    zip_buffer = io.BytesIO()
    output_dir = "output"

    # 创建 ZIP 文件
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_name in os.listdir(output_dir):
            if file_name.endswith(".srt"):
                file_path = os.path.join(output_dir, file_name)
                with open(file_path, "rb") as file:
                    zip_file.writestr(file_name, file.read())

    zip_buffer.seek(0)

    # 提供下载按钮
    st.download_button(
        label=text,
        data=zip_buffer,
        file_name="subtitles.zip",
        mime="application/zip"
    )
```

**下载内容**：

```
subtitles.zip
├── src.srt
├── trans.srt
├── src_trans.srt
└── trans_src.srt
```

---

## 🎙️ 操作三：配音

> **文件**: `st.py`  
> **函数**: `audio_processing_section()` + `process_audio()`

### 功能概述

这一步是**可选的**，为翻译后的字幕生成配音，包含 **4 个处理步骤**：

1. 生成音频任务和块
2. 提取参考音频
3. 生成和合并音频文件
4. 合并音频到视频

### 界面元素

#### 场景 1: 未处理时

```
┌──────────────────────────────────────────────────┐
│ c. Dubbing                                       │
├──────────────────────────────────────────────────┤
│                                                  │
│ This stage includes the following steps:        │
│   1. Generate audio tasks and chunks            │
│   2. Extract reference audio                    │
│   3. Generate and merge audio files             │
│   4. Merge final audio into video               │
│                                                  │
│ [Start Audio Processing]                        │
│                                                  │
└──────────────────────────────────────────────────┘
```

#### 场景 2: 处理完成后

```
┌──────────────────────────────────────────────────┐
│ c. Dubbing                                       │
├──────────────────────────────────────────────────┤
│                                                  │
│ ✅ Audio processing is complete!                │
│                                                  │
│ ┌────────────────────────────────────────────┐  │
│ │                                            │  │
│ │   🎥 Video with Dubbing Preview            │  │
│ │                                            │  │
│ └────────────────────────────────────────────┘  │
│                                                  │
│ [Delete dubbing files]                          │
│                                                  │
│ [Archive to 'history']                          │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 处理流程

```python
def audio_processing_section():
    st.header(t("c. Dubbing"))
    with st.container(border=True):
        # 显示步骤说明
        st.markdown(f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("Generate audio tasks and chunks")}<br>
            2. {t("Extract reference audio")}<br>
            3. {t("Generate and merge audio files")}<br>
            4. {t("Merge final audio into video")}
        """, unsafe_allow_html=True)

        # 检查是否已完成
        if not os.path.exists(DUB_VIDEO):  # DUB_VIDEO = "output/output_dub.mp4"
            # 未完成，显示处理按钮
            if st.button(t("Start Audio Processing")):
                process_audio()  # 执行处理
                st.rerun()  # 刷新页面
        else:
            # 已完成，显示结果
            st.success(t("Audio processing is complete!"))

            if load_key("burn_subtitles"):
                st.video(DUB_VIDEO)  # 显示带配音的视频

            # 删除配音文件按钮
            if st.button(t("Delete dubbing files")):
                delete_dubbing_files()
                st.rerun()

            # 归档按钮
            if st.button(t("Archive to 'history'")):
                cleanup()
                st.rerun()
```

### 核心处理函数

```python
def process_audio():
    """执行完整的配音流程"""

    # 步骤 1: 生成音频任务 (约 30 秒 - 1 分钟)
    with st.spinner(t("Generate audio tasks")):
        _8_1_audio_task.gen_audio_task_main()  # 规划音频任务
        _8_2_dub_chunks.gen_dub_chunks()       # 分块处理

    # 步骤 2: 提取参考音频 (约 30 秒)
    with st.spinner(t("Extract refer audio")):
        _9_refer_audio.extract_refer_audio_main()  # 提取背景音和参考音

    # 步骤 3: 生成所有音频 (约 5-20 分钟，取决于 TTS 速度)
    with st.spinner(t("Generate all audio")):
        _10_gen_audio.gen_audio()  # 调用 TTS 生成配音

    # 步骤 4: 合并音频 (约 1-2 分钟)
    with st.spinner(t("Merge full audio")):
        _11_merge_audio.merge_full_audio()  # 合并所有音频片段

    # 步骤 5: 合并到视频 (约 30 秒 - 1 分钟)
    with st.spinner(t("Merge dubbing to the video")):
        _12_dub_to_vid.merge_video_audio()  # 音频合并到视频

    # 完成！
    st.success(t("Audio processing complete! 🎇"))
    st.balloons()  # 🎈 庆祝动画
```

### 生成的文件

```
output/
└── output_dub.mp4              ← 带配音的视频（主要输出）

output/audio/
├── full_audio.wav              ← 完整配音音频
├── target_0.wav                ← 各个音频片段
├── target_1.wav
├── target_2.wav
└── ...

output/refer_audio/
├── background_0.wav            ← 背景音片段
├── background_1.wav
└── ...
```

---

## 🔄 完整工作流程

### 典型使用场景

```
1️⃣ 上传视频
   用户: 上传 "tutorial.mp4" (5 分钟教程视频)
   系统: 保存到 output/tutorial.mp4
        ↓
2️⃣ 字幕处理
   用户: 点击 "Start Processing Subtitles"
   系统:
   [0:00 - 2:00] 🎤 WhisperX 转录中...
   [2:00 - 2:30] ✂️ NLP 分割中...
   [2:30 - 3:00] 🤖 LLM 语义分割中...
   [3:00 - 6:00] 📖 摘要和翻译中...
   [6:00 - 7:00] 📏 字幕切割对齐中...
   [7:00 - 7:30] 🔗 时间戳对齐中...
   [7:30 - 8:00] 🎬 字幕烧录中...
   ✅ 完成！生成 output_sub.mp4
        ↓
3️⃣ 配音（可选）
   用户: 点击 "Start Audio Processing"
   系统:
   [0:00 - 0:30] 📋 生成音频任务...
   [0:30 - 1:00] 🎵 提取参考音频...
   [1:00 - 8:00] 🗣️ TTS 生成配音...
   [8:00 - 9:00] 🔊 合并音频...
   [9:00 - 9:30] 🎬 合并到视频...
   ✅ 完成！生成 output_dub.mp4
        ↓
4️⃣ 下载结果
   用户: 点击 "Download All Srt Files"
   系统: 下载 subtitles.zip (包含所有 SRT 文件)

   用户: 右键视频 → 下载
   系统: 下载 output_sub.mp4 或 output_dub.mp4
```

---

## ⚙️ 侧边栏设置

除了三大主要操作，VideoLingo 还提供了**侧边栏设置**面板：

```
┌─ Sidebar ──────────────────┐
│                            │
│ 🌐 Display Language        │
│    [简体中文 ▼]             │
│                            │
│ 🎯 Target Language         │
│    [简体中文]               │
│                            │
│ 🤖 LLM Provider            │
│    API Key: [**********]   │
│    Base URL: [*******]     │
│    Model: [gpt-4.1 ▼]      │
│                            │
│ 🎙️ Whisper Settings        │
│    Runtime: [local ▼]      │
│    Language: [en ▼]        │
│                            │
│ 🗣️ TTS Settings            │
│    Method: [azure_tts ▼]   │
│    Voice: [*******]        │
│                            │
│ [Save Settings]            │
│                            │
│ ─────────────────────────  │
│                            │
│ [⭐ Star on GitHub]        │
│                            │
└────────────────────────────┘
```

这些设置会保存到 `config.yaml`。

---

## 📊 状态检测逻辑

VideoLingo 通过检测**输出文件**来判断各步骤的完成状态：

```python
# 检测视频是否上传
try:
    video_file = find_video_files()  # 在 output/ 中查找视频
    # 找到 → 显示视频和删除按钮
except:
    # 未找到 → 显示上传/下载界面

# 检测字幕是否完成
if not os.path.exists(SUB_VIDEO):  # output/output_sub.mp4
    # 未完成 → 显示 "Start Processing Subtitles" 按钮
else:
    # 已完成 → 显示视频预览和下载按钮

# 检测配音是否完成
if not os.path.exists(DUB_VIDEO):  # output/output_dub.mp4
    # 未完成 → 显示 "Start Audio Processing" 按钮
else:
    # 已完成 → 显示视频预览和删除按钮
```

这种设计允许用户**断点续传**：

- 关闭浏览器后重新打开，仍能看到之前的处理结果
- 可以跳过已完成的步骤

---

## 🎨 UI/UX 特性

### 1. 进度指示

使用 `st.spinner()` 显示实时进度：

```python
with st.spinner("Using Whisper for transcription..."):
    _2_asr.transcribe()
```

**效果**：

```
⏳ Using Whisper for transcription... (旋转动画)
```

### 2. 成功提示

```python
st.success("Subtitle processing complete! 🎉")
st.balloons()  # 气球庆祝动画 🎈
```

### 3. 视频预览

```python
st.video(SUB_VIDEO)  # 直接在页面中播放视频
```

### 4. 下载按钮

```python
st.download_button(
    label="Download All Srt Files",
    data=zip_buffer,
    file_name="subtitles.zip",
    mime="application/zip"
)
```

### 5. 容器边框

```python
with st.container(border=True):
    # 内容...
```

**效果**：在内容周围添加边框，视觉分组更清晰。

### 6. 自定义按钮样式

通过 CSS 自定义按钮颜色：

```css
div.stButton > button:first-child {
  color: #144070;
  background-color: transparent;
  border: 2px solid #d0dff2;
  font-size: 1.2em;
}
div.stButton > button:hover {
  border-color: #144070;
}
```

---

## 🔧 关键技术点

### 1. 状态管理

Streamlit 是**无状态**的，每次交互都会重新运行整个脚本。VideoLingo 通过**文件系统**来持久化状态：

```python
# 检查文件是否存在来判断状态
if os.path.exists("output/output_sub.mp4"):
    # 已完成字幕处理
```

### 2. 页面重载

```python
st.rerun()  # 刷新页面
```

在以下情况下会调用：

- 上传/下载视频后
- 删除视频后
- 处理完成后
- 归档文件后

### 3. 文件上传处理

```python
uploaded_file = st.file_uploader("Or upload video", type=["mp4", "mov", ...])
if uploaded_file:
    # 清理文件名
    raw_name = uploaded_file.name.replace(' ', '_')
    clean_name = re.sub(r'[^\w\-_\.]', '', name) + ext.lower()

    # 保存文件
    with open(os.path.join(OUTPUT_DIR, clean_name), "wb") as f:
        f.write(uploaded_file.getbuffer())
```

**问题**：文件名可能包含特殊字符或空格  
**解决**：使用正则表达式清理文件名

### 4. 归档功能

```python
def cleanup():
    """将 output/ 移动到 history/ 并重命名为时间戳"""
    if os.path.exists("output"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_dir = f"history/{timestamp}"
        shutil.move("output", target_dir)
```

---

## 📝 总结

### 三大操作对比

| 操作          | 必需性  | 耗时       | 主要输出                         |
| ------------- | ------- | ---------- | -------------------------------- |
| 上传/下载视频 | ✅ 必需 | 1-5 分钟   | `output/video.mp4`               |
| 字幕翻译生成  | ✅ 必需 | 8-20 分钟  | `output_sub.mp4` + 4 个 SRT 文件 |
| 配音          | ❌ 可选 | 10-30 分钟 | `output_dub.mp4`                 |

### 典型工作流

```
用户打开浏览器
    ↓
访问 http://localhost:8501
    ↓
操作 1: 上传视频 (tutorial.mp4)
    ↓
操作 2: 点击 "Start Processing Subtitles"
    ↓
等待 10 分钟...
    ↓
下载 subtitles.zip (包含 4 个 SRT)
    ↓
(可选) 操作 3: 点击 "Start Audio Processing"
    ↓
等待 15 分钟...
    ↓
下载 output_dub.mp4
    ↓
点击 "Archive to 'history'" (归档)
    ↓
重新开始处理下一个视频
```

### 设计优势

1. **简单直观**：三步式操作，顺序清晰
2. **可视化反馈**：实时进度、视频预览、庆祝动画
3. **断点续传**：基于文件检测状态，可随时中断和恢复
4. **灵活性**：配音可选，允许仅生成字幕
5. **归档功能**：自动管理历史记录

---

**文档生成时间**: 2025-12-29  
**VideoLingo 版本**: 3.0.0
