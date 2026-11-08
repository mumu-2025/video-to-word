from __future__ import annotations

import re
import shutil
from pathlib import Path


INVALID_FS_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def which_or_raise(name: str, hint: str = "") -> str:
    path = shutil.which(name)
    if not path:
        # also check common user local bin
        candidate = Path.home() / ".local" / "bin" / name
        if candidate.is_file():
            return str(candidate)
        msg = f"Required executable not found: {name}"
        if hint:
            msg += f" ({hint})"
        raise FileNotFoundError(msg)
    return path


def safe_filename(title: str, max_len: int = 80) -> str:
    title = (title or "untitled").strip()
    title = INVALID_FS_CHARS.sub(" ", title)
    title = re.sub(r"\s+", " ", title).strip(" .")
    if not title:
        title = "untitled"
    if len(title) > max_len:
        title = title[:max_len].rstrip(" .")
    return title


def clean_paragraphs(text: str) -> list[str]:
    """Normalize ASR/subtitle text into readable paragraphs."""
    if not text:
        return []
    # Normalize newlines and whitespace
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    # Drop common ASR filler markers
    text = re.sub(r"</?\|?[^|>]+?\|>?", "", text)  # FunASR special tokens like <|zh|>
    text = text.replace("\u3000", " ")
    chunks: list[str] = []
    for block in re.split(r"\n{2,}", text):
        block = block.strip()
        if not block:
            continue
        # Join single newlines inside a block into spaces / Chinese flow
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        joined = ""
        for ln in lines:
            if not joined:
                joined = ln
            elif joined[-1] in "。！？!?；;…" or ln[0] in "「『（([":
                joined = joined + "\n" + ln
            elif re.search(r"[A-Za-z0-9]$", joined) and re.match(r"[A-Za-z0-9]", ln):
                joined = joined + " " + ln
            else:
                joined = joined + ln
        # Further split very long Chinese blocks on sentence enders
        parts = re.split(r"(?<=[。！？!?])\s*", joined)
        buf = ""
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if not buf:
                buf = p
            elif len(buf) + len(p) < 220:
                buf = buf + p
            else:
                chunks.append(buf)
                buf = p
        if buf:
            chunks.append(buf)
    return chunks
