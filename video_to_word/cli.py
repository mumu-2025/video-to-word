from __future__ import annotations

import argparse
import sys
from pathlib import Path

from video_to_word import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="video-to-word",
        description=(
            "多视频网站通用：URL/本地文件 → 音频 → 转写 → Word (.docx)。"
            " Multi-site video/audio → transcript → Word via yt-dlp + ASR."
        ),
    )
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument("--url", help="Video URL (YouTube / Bilibili / Vimeo / X / … via yt-dlp)")
    src.add_argument("--file", help="Local video or audio file path")
    p.add_argument("--out", default="./out", help="Output directory for .docx (default: ./out)")
    p.add_argument(
        "--engine",
        default="funasr",
        choices=["funasr", "faster-whisper", "whisper", "fw"],
        help="ASR engine when subtitles unavailable (default: funasr)",
    )
    p.add_argument(
        "--language",
        default="zh",
        help="Language hint: zh|en|auto (default: zh)",
    )
    p.add_argument(
        "--keep-audio",
        action="store_true",
        help="Keep extracted audio under out/audio/ (default: delete temp media)",
    )
    p.add_argument(
        "--no-subs",
        action="store_true",
        help="Do not try yt-dlp subtitles; always run ASR",
    )
    p.add_argument(
        "--force-asr",
        action="store_true",
        help="Run ASR even if subtitles were found",
    )
    p.add_argument(
        "--fw-model",
        default="small",
        help="faster-whisper model size (tiny|base|small|medium|large-v3). Default: small",
    )
    p.add_argument(
        "--list-extractors-summary",
        action="store_true",
        help="Print yt-dlp extractor coverage summary and exit",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_extractors_summary:
        from video_to_word.download import list_extractors_summary

        print(list_extractors_summary())
        return 0

    if not args.url and not args.file:
        parser.error("one of --url or --file is required (or use --list-extractors-summary)")

    from video_to_word.pipeline import run_pipeline

    result = run_pipeline(
        url=args.url,
        file=args.file,
        out_dir=Path(args.out),
        engine=args.engine,
        language=args.language,
        keep_audio=args.keep_audio,
        prefer_subs=not args.no_subs,
        fw_model=args.fw_model,
        force_asr=args.force_asr,
    )
    print(f"OK title={result.title}")
    print(f"OK source={result.source}")
    print(f"OK extractor={result.extractor or '-'}")
    print(f"OK engine={result.engine_used} subs={result.used_subtitles}")
    print(f"OK docx={result.docx_path}")
    if result.audio_kept:
        print(f"OK audio={result.audio_kept}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
