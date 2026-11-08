from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from video_to_word.asr import transcribe
from video_to_word.docx_out import write_transcript_docx
from video_to_word.download import download_url, probe_local
from video_to_word.util import clean_paragraphs


@dataclass
class PipelineResult:
    docx_path: Path
    title: str
    source: str
    extractor: str
    engine_used: str
    used_subtitles: bool
    audio_kept: Optional[Path] = None


def run_pipeline(
    *,
    url: Optional[str] = None,
    file: Optional[str] = None,
    out_dir: str | Path = "./out",
    engine: str = "funasr",
    language: str = "zh",
    keep_audio: bool = False,
    prefer_subs: bool = True,
    fw_model: str = "small",
    force_asr: bool = False,
) -> PipelineResult:
    if not url and not file:
        raise ValueError("Provide --url or --file")
    if url and file:
        raise ValueError("Provide only one of --url or --file")

    work_dir: Optional[Path] = None
    try:
        if file:
            media = probe_local(Path(file))
        else:
            media = download_url(url, prefer_subs=prefer_subs, language=language)
        work_dir = media.work_dir

        used_subs = False
        engine_used = "subtitles"
        if prefer_subs and media.subtitle_text and not force_asr:
            raw = media.subtitle_text
            used_subs = True
        else:
            raw = transcribe(
                media.audio_path,
                engine=engine,
                language=language,
                fw_model=fw_model,
            )
            engine_used = engine

        paras = clean_paragraphs(raw)
        docx_path = write_transcript_docx(
            title=media.title,
            paragraphs=paras,
            source=media.webpage_url or media.source,
            extractor=media.extractor,
            engine=engine_used,
            out_dir=Path(out_dir),
        )

        kept = None
        if keep_audio and media.audio_path.exists():
            keep_dir = Path(out_dir) / "audio"
            keep_dir.mkdir(parents=True, exist_ok=True)
            dest = keep_dir / media.audio_path.name
            shutil.copy2(media.audio_path, dest)
            kept = dest

        return PipelineResult(
            docx_path=docx_path,
            title=media.title,
            source=media.webpage_url or media.source,
            extractor=media.extractor,
            engine_used=engine_used,
            used_subtitles=used_subs,
            audio_kept=kept,
        )
    finally:
        if work_dir and work_dir.exists() and not keep_audio:
            shutil.rmtree(work_dir, ignore_errors=True)
