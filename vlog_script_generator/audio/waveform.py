from __future__ import annotations

from pathlib import Path


def waveform_hint(audio_path: str | Path | None) -> str:
    if not audio_path:
        return "未生成音频波形"
    return "已提取音频，可在后续版本生成能量波形辅助判断情绪"

