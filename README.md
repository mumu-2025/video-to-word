# video-to-word

**多视频网站通用：URL → 音频 → 转写 → Word（.docx）**  
**Multi-site video URL/file → audio → transcript → Word for agents**

> 一句话价值：把 YouTube / Bilibili / Vimeo / X 等 **yt-dlp 能解的视频链接**（或本地音视频）一键变成可导出的逐字稿 Word，并附带可加载到 Cursor / Codex / Claude Code / Grok Bot 的 Agent Skill。

## 功能

- **多站点**：不绑死 YouTube；走 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 提取器（本机可用 `yt-dlp --list-extractors` 查看完整列表，通常 1800+）。
- **字幕优先**：有官方/自动字幕时先用字幕，没有再 ASR。
- **ASR**：默认 **FunASR**（中文强）；可选 **faster-whisper**。
- **输出**：`{标题}-逐字转录.docx`，尽量保留视频原标题（含中文）。
- **Agent Skill**：`skill/SKILL.md` 可拷贝到 `~/.agents/skills/video-to-word/`。

## 常见平台（摘要）

| 平台 | 典型可用性 | 说明 |
|------|------------|------|
| YouTube | 通常可用 | 短视频/Shorts 冒烟已测（见下方矩阵） |
| Bilibili | 视网络/地区 | 公开稿件通常可抽音轨；大会员/地区限制会失败 |
| Vimeo | 公开视频通常可用 | 密码/私有不可 |
| X / Twitter | 公开视频通常可用 | 登录墙/地区可能失败 |
| TikTok / 抖音 | 不稳定 | 风控、登录、地区常见失败 |
| 优酷 / 爱奇艺 / 腾讯视频 | 经常失败 | DRM / 登录 / 付费墙 — **不绕过** |

完整列表：

```bash
yt-dlp --list-extractors
# 或
video-to-word --list-extractors-summary
```

## 安装

### 系统依赖

```bash
# yt-dlp
pipx install yt-dlp   # 或: curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o ~/.local/bin/yt-dlp && chmod +x ~/.local/bin/yt-dlp

# ffmpeg
sudo apt-get install -y ffmpeg   # macOS: brew install ffmpeg
```

### Python 包

```bash
git clone https://github.com/mumu-2025/video-to-word.git
cd video-to-word
pip install -r requirements.txt          # python-docx
# 可选：editable
pip install -e .
```

### ASR 引擎（任选）

```bash
# FunASR（默认，中文）— 可用独立 venv
python3 -m venv /path/to/funasr && source /path/to/funasr/bin/activate
pip install funasr torch torchaudio modelscope
export VIDEO_TO_WORD_FUNASR_VENV=/path/to/funasr

# 或 faster-whisper（更轻、多语）
python3 -m venv /path/to/fw && source /path/to/fw/bin/activate
pip install faster-whisper
export VIDEO_TO_WORD_FW_VENV=/path/to/fw
```

本仓库开发机默认约定：

- FunASR: `/workspace/.venvs/funasr`
- faster-whisper: `/workspace/.venvs/faster-whisper`

### 安装 Agent Skill（Cursor / Codex / Claude Code 等）

```bash
mkdir -p ~/.agents/skills/video-to-word
cp skill/SKILL.md ~/.agents/skills/video-to-word/SKILL.md
# 可选软链
ln -sfn ~/.agents/skills/video-to-word ~/.claude/skills/video-to-word
ln -sfn ~/.agents/skills/video-to-word ~/.cursor/skills/video-to-word
```

## 用法

```bash
# 任意 yt-dlp URL
./bin/video-to-word --url 'https://www.youtube.com/watch?v=…' --out ./out

# Bilibili
./bin/video-to-word --url 'https://www.bilibili.com/video/BV…' --language zh

# 本地文件
./bin/video-to-word --file ./talk.mp4 --out ./out --engine funasr

# 强制 ASR / 换引擎
./bin/video-to-word --url '…' --force-asr --engine faster-whisper --fw-model base

# 保留音频
./bin/video-to-word --url '…' --keep-audio

# 查看提取器摘要
./bin/video-to-word --list-extractors-summary
```

也可用：

```bash
PYTHONPATH=. python3 -m video_to_word --help
```

## 架构

```
URL / local file
    │
    ├─(URL)── yt-dlp  (--write-sub / --write-auto-sub 优先)
    │            └─ -x 抽音频 (+ ffmpeg 16k mono wav)
    ├─(file)─ ffmpeg 抽音频（若已是音频则直用）
    │
    ├─ 有可用字幕 ──► 清洗段落
    └─ 无字幕 ──────► FunASR 或 faster-whisper
                         │
                         ▼
                   python-docx  →  {标题}-逐字转录.docx
```

## 各平台如何加载 skill（诚实说明）

| 环境 | 能否原生加载本 skill？ | 怎么做 |
|------|------------------------|--------|
| **Cursor / Codex / Claude Code / 支持 Agent Skills 目录的工具** | ✅ 可以 | 拷贝 `skill/SKILL.md` 到 `~/.agents/skills/video-to-word/`（或产品文档指定的 skills 目录） |
| **Grok Bot（本助手）** | ✅ 可以（用户技能） | 在本助手用 **UpdateSkill / Files** 写入 skill 正文；**不是** GitHub 一键安装到 grok.com 网页端 |
| **ChatGPT** | ❌ 不能 `git clone` 成官方 Custom GPT「原生 skill 文件夹」 | 可把 README/SKILL 流程摘要粘贴进 **Custom GPT Instructions**；若自建 Actions/MCP 再调本 CLI；能力受 GPT 工具边界限制 |
| **Gemini（Gems / AI Studio）** | ❌ 同样没有原生 Agent Skills 目录 | 粘贴说明书到 Gem instructions，或自建工具/扩展调用本 CLI |

**GitHub 仓库本身 = 代码 + 文档分发渠道**；各聊天产品是否认 Agent Skills 文件夹，是产品能力，不是 `git push` 自动完成的。

## 依赖与硬件

- 中文 FunASR / SenseVoice 模型**体积大**（首次运行会下载，需磁盘与耐心）。
- faster-whisper `tiny`/`base` 更适合冒烟与轻量机。
- CPU 可跑；有 CUDA 时 faster-whisper/FunASR 可更快（需自行配置）。
- 默认**删除**临时音视频，避免多 GB 残留。

## 合规

- 仅处理**你有权使用**的内容（自有素材、授权、或平台允许的个人合理使用范围）。
- **不**绕过付费墙、DRM、登录墙、地区限制。
- 站点失败时如实记录，不提供破解方案。

## 冒烟矩阵（开发记录，2026-11-08 Asia/Shanghai）

| 站点 | 样例 | 结果 | 路径 |
|------|------|------|------|
| YouTube | `jNQXAC9IVRw`《Me at the zoo》19s | ✅ 字幕路径成功；✅ `--force-asr` + faster-whisper tiny 成功 | URL→docx |
| Internet Archive | `testmp3testfile` ~12s | ✅ faster-whisper 转写成功 | URL→docx |
| 本地 wav | `--file` | ✅ | file→docx |
| Bilibili | 公开 BV | ❌ HTTP 412 Precondition Failed（机房出口/风控，非破解范围） | — |
| Vimeo | 公开片 | ❌ TLS fingerprint blocked（缺 impersonation 依赖；不做不安全绕过） | — |

失败站点会标明原因（geo / login / DRM / TLS / 风控），**不做绕过**。更完整记录见 knowledge note。

## License

MIT
