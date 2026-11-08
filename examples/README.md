# Examples

```bash
# YouTube short / any yt-dlp URL
video-to-word --url 'https://www.youtube.com/watch?v=XXXX' --out ./out

# Bilibili
video-to-word --url 'https://www.bilibili.com/video/BVxxxx' --out ./out --language zh

# Local file
video-to-word --file ./sample.mp4 --out ./out --engine faster-whisper --language auto

# Force ASR even if subs exist
video-to-word --url '…' --force-asr --engine funasr

# Keep temp audio
video-to-word --url '…' --keep-audio
```

Smoke inputs used in development (short public demos) are recorded in the knowledge note / README supported matrix — replace with your own licensed content for production.
