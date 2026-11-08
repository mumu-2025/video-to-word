---
name: video-to-word
description: Turn a video URL or local media file from many sites (YouTube, Bilibili, Vimeo, X/Twitter, etc. via yt-dlp) into a cleaned Chinese/English transcript Word (.docx). Use whenever the user pastes a video link and asks for 转写、逐字稿、字幕整理、Word、docx、transcript, or audio-to-text from that video.
license: MIT
metadata:
  version: "0.1.0"
  tags:
    - transcript
    - video
    - word
    - asr
    - yt-dlp
---

# video-to-word（多视频网站通用：URL→音频→转写→Word）

## When to use

- User pastes a **video URL** (YouTube / Bilibili / Vimeo / X / …) and wants a **Word transcript**.
- User provides a **local video/audio file** and wants `.docx` 逐字稿.
- User asks to reuse the past flow: 视频网址 → 提取声音 → 语音转文字 → Word 导出.

## Do not use

- To bypass paywalls, DRM, private/login-only downloads, or content the user is not allowed to copy.
- For politics / brand-war content the user has marked off-limits.
- As a bulk pirate downloader.

## Prerequisites (box / machine)

- CLI repo: `/workspace/repos/video-to-word` (or clone of this project)
- `yt-dlp`, `ffmpeg` on PATH
- FunASR venv (default): `/workspace/.venvs/funasr` — or set `VIDEO_TO_WORD_FUNASR_VENV`
- Optional faster-whisper venv: `/workspace/.venvs/faster-whisper` — or `VIDEO_TO_WORD_FW_VENV`
- `python-docx` available to the orchestrating Python

## Steps

1. **Confirm intent**: user wants transcript/Word from a URL or file. Note language (`zh` default, or `en`/`auto`).
2. **Prefer subtitles first** (faster, often cleaner):
   ```bash
   cd /workspace/repos/video-to-word
   ./bin/video-to-word --url 'URL' --out ./out --language zh
   ```
   The CLI tries `yt-dlp --write-sub --write-auto-sub` before ASR.
3. **If no usable subs**, ASR runs automatically:
   - Default: `--engine funasr` (Chinese-strong)
   - Lighter / multilingual: `--engine faster-whisper --fw-model small`
   - Force ASR: `--force-asr` or `--no-subs`
4. **Local file**:
   ```bash
   ./bin/video-to-word --file '/path/to/video.mp4' --out ./out --engine funasr
   ```
5. **Return** the `.docx` path to the user. Title keeps the original (often Chinese) metadata title when yt-dlp provides it.
6. **Temp media**: deleted by default. Only pass `--keep-audio` if the user asked to keep audio.
7. **Delivery (optional, configurable)**: if chat download fails and the user has a preferred delivery channel (e.g. QQ / email on file), offer that channel — **do not hard-code or send** without an explicit ask this turn.

## Failure handling

- Geo-block / login / DRM / extractor missing: report the **site + error honestly**. Do not attempt bypasses.
- Huge models missing on first FunASR run: allow download once, or fall back to `--engine faster-whisper --fw-model tiny|base` for a quick pass, then tell the user.
- Multi-GB media: never leave downloads lying around; rely on default temp cleanup.

## Output expectations

- File name: `{safe_title}-逐字转录.docx` under `--out` (default `./out`)
- Document contains title, source URL, extractor, engine, Asia/Shanghai timestamp, then cleaned paragraphs.

## Related

- Full README in the GitHub repo documents ChatGPT / Gemini loading limits (instructions paste / custom tools — **not** native Agent Skills folders).
