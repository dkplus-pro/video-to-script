from __future__ import annotations

import subprocess
from pathlib import Path

from vlog_script_generator.models import ensure_dir


def extract_audio(video_path: str | Path, output_root: str | Path, sample_rate: int = 16000, force: bool = False) -> Path | None:
    target = Path(video_path)
    out_dir = ensure_dir(Path(output_root) / target.stem)
    wav_path = out_dir / "audio.wav"
    if wav_path.exists() and not force:
        return wav_path
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(target),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(sample_rate),
        "-ac",
        "1",
        str(wav_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and wav_path.exists():
            return wav_path
    except Exception:
        return None
    return None

