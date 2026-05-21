from __future__ import annotations

from pathlib import Path


def frame_quality(image_path: str | Path) -> tuple[float | None, float | None, str]:
    try:
        import cv2

        image = cv2.imread(str(image_path))
        if image is None:
            return None, None, "无法读取帧图片"
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        brightness = float(gray.mean())
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        return brightness, blur_score, ""
    except Exception as exc:
        return None, None, f"质量检测跳过：{exc}"


def classify_frame(brightness: float | None, blur_score: float | None, config: dict) -> str:
    frames_cfg = config.get("frames", {})
    if brightness is not None and brightness < float(frames_cfg.get("blackThreshold", 12)):
        return "黑屏帧"
    if blur_score is not None and blur_score < float(frames_cfg.get("blurThreshold", 45)):
        return "模糊帧"
    return ""

