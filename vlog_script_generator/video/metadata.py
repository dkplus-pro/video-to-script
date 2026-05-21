from __future__ import annotations

import json
import subprocess
from pathlib import Path

from vlog_script_generator.models import VideoMetadata


def _probe_with_ffprobe(path: Path) -> VideoMetadata | None:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,duration",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        data = json.loads(result.stdout or "{}")
        stream = (data.get("streams") or [{}])[0]
        fmt = data.get("format") or {}
        duration = float(stream.get("duration") or fmt.get("duration") or 0)
        fps_raw = stream.get("r_frame_rate") or "0/1"
        num, den = (fps_raw.split("/") + ["1"])[:2]
        fps = float(num) / float(den or 1)
        return VideoMetadata(
            file_name=path.name,
            path=str(path),
            duration=duration,
            width=int(stream.get("width") or 0),
            height=int(stream.get("height") or 0),
            fps=fps,
            readable=True,
        )
    except Exception:
        return None


def _probe_with_cv2(path: Path) -> VideoMetadata | None:
    try:
        import cv2

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return None
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
        frames = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = frames / fps if fps > 0 else 0
        meta = VideoMetadata(
            file_name=path.name,
            path=str(path),
            duration=duration,
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0),
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0),
            fps=fps,
            readable=True,
        )
        cap.release()
        return meta
    except Exception:
        return None


def read_metadata(path: str | Path) -> VideoMetadata:
    target = Path(path)
    meta = _probe_with_ffprobe(target) or _probe_with_cv2(target)
    if meta is None:
        return VideoMetadata(file_name=target.name, path=str(target), readable=False, waste_reason="无法读取视频元信息")
    if meta.duration <= 0 or meta.width <= 0 or meta.height <= 0:
        meta.suspected_waste = True
        meta.waste_reason = "视频时长或分辨率异常"
    return meta

