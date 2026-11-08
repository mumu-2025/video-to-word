from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


DEFAULT_FUNASR_VENV = Path("/workspace/.venvs/funasr")
DEFAULT_FW_VENV = Path("/workspace/.venvs/faster-whisper")


def _venv_python(venv: Path) -> Optional[Path]:
    for name in ("python", "python3"):
        p = venv / "bin" / name
        if p.is_file():
            return p
    return None


def transcribe_funasr(
    audio_path: Path,
    *,
    language: str = "zh",
    venv: Optional[Path] = None,
) -> str:
    """Run FunASR in a subprocess using the dedicated venv when available."""
    venv = venv or Path(os.environ.get("VIDEO_TO_WORD_FUNASR_VENV", str(DEFAULT_FUNASR_VENV)))
    py = _venv_python(venv) or Path(sys.executable)
    # Prefer SenseVoiceSmall (multilingual, lighter) then paraformer-zh
    script = r'''
import json, sys
audio = sys.argv[1]
lang = sys.argv[2]
from funasr import AutoModel

text = ""
last_err = None
for model_id, kwargs in [
    ("iic/SenseVoiceSmall", {"vad_model": "fsmn-vad", "vad_kwargs": {"max_single_segment_time": 30000}}),
    ("paraformer-zh", {"vad_model": "fsmn-vad", "punc_model": "ct-punc"}),
]:
    try:
        model = AutoModel(model=model_id, disable_update=True, **kwargs)
        res = model.generate(input=audio, batch_size_s=60, language=lang if lang != "auto" else "auto")
        if isinstance(res, list) and res:
            item = res[0]
            if isinstance(item, dict):
                text = item.get("text") or item.get("preds") or ""
            else:
                text = str(item)
        else:
            text = str(res)
        if text:
            break
    except Exception as e:
        last_err = e
        continue
if not text and last_err:
    raise SystemExit(f"FunASR failed: {last_err}")
# SenseVoice may wrap with tags; strip later in cleaner
print(text)
'''
    env = os.environ.copy()
    # avoid interactive prompts
    env.setdefault("MODELSCOPE_ENVIRONMENT", "offline")
    # Allow download if missing — FunASR needs models on first run
    env.pop("MODELSCOPE_ENVIRONMENT", None)
    proc = subprocess.run(
        [str(py), "-c", script, str(audio_path), language],
        capture_output=True,
        text=True,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "FunASR transcription failed.\n"
            f"python={py}\nstdout={proc.stdout[-1500:]}\nstderr={proc.stderr[-2000:]}"
        )
    return (proc.stdout or "").strip()


def transcribe_faster_whisper(
    audio_path: Path,
    *,
    language: str = "auto",
    model_size: str = "small",
    venv: Optional[Path] = None,
) -> str:
    venv = venv or Path(os.environ.get("VIDEO_TO_WORD_FW_VENV", str(DEFAULT_FW_VENV)))
    py = _venv_python(venv) or Path(sys.executable)
    script = r'''
import sys
audio = sys.argv[1]
lang = sys.argv[2]
size = sys.argv[3]
from faster_whisper import WhisperModel
model = WhisperModel(size, device="cpu", compute_type="int8")
kwargs = {"vad_filter": True}
if lang and lang != "auto":
    kwargs["language"] = lang
segments, info = model.transcribe(audio, **kwargs)
parts = []
for seg in segments:
    t = (seg.text or "").strip()
    if t:
        parts.append(t)
print("\n".join(parts))
'''
    proc = subprocess.run(
        [str(py), "-c", script, str(audio_path), language, model_size],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "faster-whisper transcription failed.\n"
            f"python={py}\nstdout={proc.stdout[-1500:]}\nstderr={proc.stderr[-2000:]}"
        )
    return (proc.stdout or "").strip()


def transcribe(
    audio_path: Path,
    *,
    engine: str = "funasr",
    language: str = "zh",
    fw_model: str = "small",
) -> str:
    engine = (engine or "funasr").lower()
    if engine in {"funasr", "sensevoice", "paraformer"}:
        return transcribe_funasr(audio_path, language=language)
    if engine in {"faster-whisper", "whisper", "fw"}:
        return transcribe_faster_whisper(audio_path, language=language, model_size=fw_model)
    raise ValueError(f"Unknown ASR engine: {engine}")
