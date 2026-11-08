from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from docx import Document
from docx.shared import Pt

from video_to_word.util import clean_paragraphs, safe_filename


def write_transcript_docx(
    *,
    title: str,
    paragraphs: list[str] | None = None,
    raw_text: str = "",
    source: str = "",
    extractor: str = "",
    engine: str = "",
    out_dir: Path,
    suffix: str = "逐字转录",
) -> Path:
    paras = paragraphs if paragraphs is not None else clean_paragraphs(raw_text)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{safe_filename(title)}-{suffix}.docx"
    out_path = out_dir / fname

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Microsoft YaHei"
    style.font.size = Pt(12)

    doc.add_heading(title, level=1)
    meta_lines = []
    if source:
        meta_lines.append(f"来源 / Source: {source}")
    if extractor:
        meta_lines.append(f"提取器 / Extractor: {extractor}")
    if engine:
        meta_lines.append(f"转写引擎 / Engine: {engine}")
    now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M Asia/Shanghai")
    meta_lines.append(f"生成时间 / Generated: {now}")
    doc.add_paragraph("\n".join(meta_lines))
    doc.add_paragraph("")

    if not paras:
        doc.add_paragraph("（无可转写文本 / No transcript text）")
    else:
        for p in paras:
            doc.add_paragraph(p)

    doc.save(str(out_path))
    return out_path
