# Changelog

## 0.1.0 — 2026-11-08

- First release: multi-site `URL|file → audio → transcript → Word (.docx)`.
- Download/extract via **yt-dlp** (`-x`) + **ffmpeg** (any extractor yt-dlp supports).
- Prefer official/auto subtitles when available; fall back to ASR.
- ASR engines: **FunASR** (default, Chinese-strong) and **faster-whisper** (optional).
- Agent Skill (`skill/SKILL.md`) for Cursor / Codex / Claude Code / Grok Bot local skills.
- Honest platform loading notes for ChatGPT / Gemini (instructions paste / custom tools, not native skill folders).
