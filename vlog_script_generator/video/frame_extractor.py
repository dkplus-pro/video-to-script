from __future__ import annotations

import math
import subprocess
from pathlib import Path

from vlog_script_generator.models import ExtractedFrame, VideoMetadata, ensure_dir
from vlog_script_generator.video.quality_filter import classify_frame, frame_quality


def select_timestamps(duration: float, min_frames: int = 6, max_frames: int = 24) -> list[float]:
    if duration <= 0:
        return [0.0]
    if duration <= 60:
        count = min(max_frames, max(min_frames, math.ceil(duration / 8)))
    elif duration <= 180:
        count = min(max_frames, max(9, math.ceil(duration / 15)))
    else:
        count = max_frames
    step = duration / (count + 1)
    return [round(step * (i + 1), 2) for i in range(count)]


def _extract_with_cv2(video_path: Path, timestamps: list[float], output_dir: Path, quality: int) -> list[Path]:
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")
    paths: list[Path] = []
    for index, ts in enumerate(timestamps, start=1):
        cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        frame_path = output_dir / f"frame_{index:03d}_{int(ts * 1000):08d}ms.jpg"
        cv2.imwrite(str(frame_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        paths.append(frame_path)
    cap.release()
    return paths


def _extract_with_ffmpeg(video_path: Path, timestamps: list[float], output_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for index, ts in enumerate(timestamps, start=1):
        frame_path = output_dir / f"frame_{index:03d}_{int(ts * 1000):08d}ms.jpg"
        cmd = ["ffmpeg", "-y", "-ss", str(ts), "-i", str(video_path), "-frames:v", "1", "-q:v", "3", str(frame_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and frame_path.exists():
            paths.append(frame_path)
    return paths


def extract_frames_for_video(
    video_path: str | Path,
    metadata: VideoMetadata,
    output_root: str | Path,
    config: dict,
    force: bool = False,
) -> list[ExtractedFrame]:
    target = Path(video_path)
    video_dir = ensure_dir(Path(output_root) / target.stem)
    min_frames = int(config.get("frames", {}).get("minFrames", 6))
    max_frames = int(config.get("frames", {}).get("maxFrames", 24))
    timestamps = select_timestamps(metadata.duration, min_frames, max_frames)
    quality = int(config.get("frames", {}).get("jpegQuality", 88))

    if not force:
        cached = sorted(video_dir.glob("frame_*.jpg"))
        if cached:
            return [_frame_record(metadata.file_name, p, config) for p in cached]

    for old in video_dir.glob("frame_*.jpg"):
        old.unlink()

    try:
        frame_paths = _extract_with_cv2(target, timestamps, video_dir, quality)
    except Exception:
        frame_paths = _extract_with_ffmpeg(target, timestamps, video_dir)

    records = [_frame_record(metadata.file_name, p, config) for p in frame_paths]
    usable = [item for item in records if not item.skipped_reason]
    return usable or records


def _frame_record(video_file: str, path: Path, config: dict) -> ExtractedFrame:
    ts = 0.0
    try:
        marker = path.stem.split("_")[-1].replace("ms", "")
        ts = int(marker) / 1000
    except Exception:
        pass
    brightness, blur_score, error = frame_quality(path)
    skipped = error or classify_frame(brightness, blur_score, config)
    return ExtractedFrame(video_file=video_file, time_seconds=ts, path=str(path), brightness=brightness, blur_score=blur_score, skipped_reason=skipped)

