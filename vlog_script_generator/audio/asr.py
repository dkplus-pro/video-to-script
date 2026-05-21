from __future__ import annotations

from pathlib import Path

from vlog_script_generator.audio.extractor import extract_audio
from vlog_script_generator.models import AsrSegment, ensure_dir
from vlog_script_generator.storage.cache import write_json


def transcribe_video(video_path: str | Path, output_root: str | Path, config: dict, force: bool = False) -> list[AsrSegment]:
    provider = config.get("audio", {}).get("asrProvider", "none")
    video = Path(video_path)
    out_dir = ensure_dir(Path(output_root) / video.stem)
    asr_path = out_dir / "asr.json"
    if asr_path.exists() and not force:
        import json

        data = json.loads(asr_path.read_text(encoding="utf-8"))
        return [AsrSegment(**item) for item in data.get("segments", [])]

    audio_path = extract_audio(video, Path(output_root) / "_audio", int(config.get("audio", {}).get("sampleRate", 16000)), force)
    segments: list[AsrSegment] = []
    if provider == "faster-whisper" and audio_path:
        segments = _transcribe_faster_whisper(audio_path, config)
    write_json(asr_path, {"video": video.name, "provider": provider, "segments": [s.to_dict() for s in segments]})
    return segments


def _transcribe_faster_whisper(audio_path: Path, config: dict) -> list[AsrSegment]:
    try:
        from faster_whisper import WhisperModel

        model_name = config.get("audio", {}).get("whisperModel", "small")
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(audio_path), language="zh")
        return [AsrSegment(start=float(seg.start), end=float(seg.end), text=seg.text.strip()) for seg in segments]
    except Exception:
        return []

