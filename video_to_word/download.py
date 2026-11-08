from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from video_to_word.util import which_or_raise


@dataclass
class MediaInfo:
    title: str
    audio_path: Path
    source: str  # url or file
    extractor: str = ""
    webpage_url: str = ""
    duration: Optional[float] = None
    subtitle_text: str = ""
    work_dir: Optional[Path] = None  # temp dir to clean


def _yt_dlp() -> str:
    return which_or_raise(
        "yt-dlp",
        hint="Install: https://github.com/yt-dlp/yt-dlp#installation",
    )


def _ffmpeg() -> str:
    return which_or_raise("ffmpeg", hint="Install ffmpeg from your package manager")


def probe_local(path: Path) -> MediaInfo:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Local file not found: {path}")
    title = path.stem
    suffix = path.suffix.lower()
    audio_exts = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma"}
    if suffix in audio_exts:
        return MediaInfo(title=title, audio_path=path, source=str(path))
    # Extract audio via ffmpeg into a temp wav
    work = Path(tempfile.mkdtemp(prefix="v2w-"))
    out = work / "audio.wav"
    cmd = [
        _ffmpeg(),
        "-y",
        "-i",
        str(path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return MediaInfo(title=title, audio_path=out, source=str(path), work_dir=work)


def _vtt_or_srt_to_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        if line.isdigit():
            continue
        if "-->" in line:
            continue
        # strip simple tags
        import re

        line = re.sub(r"<[^>]+>", "", line)
        if line and (not lines or lines[-1] != line):
            lines.append(line)
    return "\n".join(lines)


def download_url(
    url: str,
    *,
    prefer_subs: bool = False,
    language: str = "auto",
    work_dir: Optional[Path] = None,
) -> MediaInfo:
    """Download best audio via yt-dlp. Subtitles only when prefer_subs=True (opt-in)."""
    yt = _yt_dlp()
    work = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="v2w-"))
    work.mkdir(parents=True, exist_ok=True)
    outtmpl = str(work / "%(title).80B [%(id)s].%(ext)s")

    meta_cmd = [yt, "--dump-single-json", "--no-playlist", "--no-warnings", url]
    meta_proc = subprocess.run(meta_cmd, capture_output=True, text=True)
    meta: dict = {}
    if meta_proc.returncode == 0 and meta_proc.stdout.strip():
        try:
            meta = json.loads(meta_proc.stdout)
        except json.JSONDecodeError:
            meta = {}

    title = (meta.get("title") or meta.get("fulltitle") or "").strip()
    extractor = str(meta.get("extractor_key") or meta.get("extractor") or "")
    webpage_url = str(meta.get("webpage_url") or url)
    duration = meta.get("duration")

    # Fallback metadata when JSON dump is flaky (e.g. YouTube without JS runtime)
    if not title or not extractor:
        print_cmd = [
            yt,
            "--no-playlist",
            "--no-warnings",
            "--print",
            "%(extractor_key)s\t%(title)s\t%(duration)s\t%(webpage_url)s",
            url,
        ]
        print_proc = subprocess.run(print_cmd, capture_output=True, text=True)
        line = (print_proc.stdout or "").strip().splitlines()
        if line:
            parts = line[-1].split("\t")
            if len(parts) >= 4:
                extractor = extractor or parts[0]
                title = title or parts[1]
                if duration is None and parts[2] not in {"", "NA", "None"}:
                    try:
                        duration = float(parts[2])
                    except ValueError:
                        pass
                webpage_url = webpage_url or parts[3]
    if not title:
        title = "untitled"

    subtitle_text = ""
    if prefer_subs:
        sub_langs = []
        if language and language != "auto":
            sub_langs.append(language)
        sub_langs.extend(["zh-Hans", "zh-CN", "zh", "zh-TW", "en", "en-US"])
        # unique preserve order
        seen = set()
        langs = []
        for L in sub_langs:
            if L not in seen:
                seen.add(L)
                langs.append(L)
        sub_cmd = [
            yt,
            "--skip-download",
            "--write-sub",
            "--write-auto-sub",
            "--sub-langs",
            ",".join(langs),
            "--convert-subs",
            "srt",
            "--no-playlist",
            "--no-warnings",
            "-o",
            outtmpl,
            url,
        ]
        subprocess.run(sub_cmd, capture_output=True, text=True)
        # pick best subtitle file
        candidates = sorted(work.glob("*.srt")) + sorted(work.glob("*.vtt"))
        # prefer zh then en
        def score(p: Path) -> int:
            name = p.name.lower()
            if "zh-hans" in name or "zh-cn" in name:
                return 0
            if ".zh." in name or name.endswith(".zh.srt") or ".zh-" in name:
                return 1
            if "zh-tw" in name or "zh-hant" in name:
                return 2
            if ".en." in name or "en-us" in name or "en-gb" in name:
                return 3
            return 9

        if candidates:
            best = sorted(candidates, key=score)[0]
            subtitle_text = _vtt_or_srt_to_text(best)

    # Extract audio only
    audio_outtmpl = str(work / "audio.%(ext)s")
    dl_cmd = [
        yt,
        "-x",
        "--audio-format",
        "wav",
        "--audio-quality",
        "0",
        "--no-playlist",
        "--no-warnings",
        "-o",
        audio_outtmpl,
        url,
    ]
    # postprocessor args for 16k mono if possible
    dl_cmd.extend(["--postprocessor-args", "ffmpeg:-ar 16000 -ac 1"])
    proc = subprocess.run(dl_cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        # fallback without forced wav
        dl_cmd2 = [
            yt,
            "-x",
            "--audio-format",
            "m4a",
            "--no-playlist",
            "--no-warnings",
            "-o",
            audio_outtmpl,
            url,
        ]
        proc2 = subprocess.run(dl_cmd2, capture_output=True, text=True)
        if proc2.returncode != 0:
            err = (proc.stderr or proc.stdout or "")[-2000:]
            err2 = (proc2.stderr or proc2.stdout or "")[-2000:]
            raise RuntimeError(
                f"yt-dlp audio download failed for {url}\n--- attempt1 ---\n{err}\n--- attempt2 ---\n{err2}"
            )

    audio_files = list(work.glob("audio.*"))
    # also accept any media if naming differed
    if not audio_files:
        audio_files = [
            p
            for p in work.iterdir()
            if p.suffix.lower() in {".wav", ".m4a", ".mp3", ".opus", ".webm", ".ogg"}
        ]
    if not audio_files:
        raise RuntimeError(f"No audio file produced in {work}")
    audio_path = audio_files[0]

    # Ensure wav 16k mono for ASR friendliness when not already
    if audio_path.suffix.lower() != ".wav":
        wav = work / "audio_16k.wav"
        ff = [
            _ffmpeg(),
            "-y",
            "-i",
            str(audio_path),
            "-ar",
            "16000",
            "-ac",
            "1",
            str(wav),
        ]
        subprocess.run(ff, check=True, capture_output=True)
        audio_path = wav

    if not title or title == "untitled":
        # try from filename
        title = audio_path.stem

    return MediaInfo(
        title=title,
        audio_path=audio_path,
        source=url,
        extractor=extractor,
        webpage_url=webpage_url,
        duration=float(duration) if duration is not None else None,
        subtitle_text=subtitle_text,
        work_dir=work,
    )


def list_extractors_summary(limit: int = 40) -> str:
    yt = _yt_dlp()
    proc = subprocess.run([yt, "--list-extractors"], capture_output=True, text=True)
    lines = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()]
    total = len(lines)
    common = [
        "youtube",
        "BiliBili",
        "BiliBiliBangumi",
        "vimeo",
        "twitter",
        "TikTok",
        "facebook",
        "Instagram",
        "douyin",
        "ixigua",
        "Iqiyi",
        "TencentVideo",
        "Youku",
    ]
    present = [c for c in common if any(c.lower() == ln.lower() or c.lower() in ln.lower() for ln in lines)]
    head = ", ".join(lines[:limit])
    return (
        f"yt-dlp extractors: {total} total.\n"
        f"Common platforms detected in this build: {', '.join(present) or '(run yt-dlp --list-extractors)'}\n"
        f"First {limit}: {head}…"
    )
