from __future__ import annotations

from pathlib import Path

from vlog_script_generator.models import ExtractedFrame, Filmstrip, ensure_dir


def make_filmstrips(
    frames: list[ExtractedFrame],
    output_root: str | Path,
    frames_per_strip: int = 9,
    force: bool = False,
) -> list[Filmstrip]:
    if not frames:
        return []
    from PIL import Image, ImageDraw

    grouped: dict[str, list[ExtractedFrame]] = {}
    for frame in frames:
        grouped.setdefault(frame.video_file, []).append(frame)

    output = ensure_dir(output_root)
    strips: list[Filmstrip] = []
    for video_file, items in grouped.items():
        items = sorted(items, key=lambda item: item.time_seconds)
        video_dir = ensure_dir(output / Path(video_file).stem)
        chunks = [items[i : i + frames_per_strip] for i in range(0, len(items), frames_per_strip)]
        for index, chunk in enumerate(chunks, start=1):
            strip_path = video_dir / f"filmstrip_{index:03d}.jpg"
            if strip_path.exists() and not force:
                strips.append(_record(video_file, strip_path, chunk))
                continue
            _compose_strip(chunk, strip_path)
            strips.append(_record(video_file, strip_path, chunk))
    return strips


def _compose_strip(frames: list[ExtractedFrame], output_path: Path) -> None:
    from PIL import Image, ImageDraw

    thumb_w, thumb_h, label_h = 320, 180, 34
    columns = 3 if len(frames) > 3 else len(frames)
    rows = (len(frames) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "white")
    draw = ImageDraw.Draw(canvas)
    for idx, frame in enumerate(frames):
        row, col = divmod(idx, columns)
        x, y = col * thumb_w, row * (thumb_h + label_h)
        try:
            image = Image.open(frame.path).convert("RGB")
            image.thumbnail((thumb_w, thumb_h))
            px = x + (thumb_w - image.width) // 2
            py = y + (thumb_h - image.height) // 2
            canvas.paste(image, (px, py))
        except Exception:
            draw.rectangle([x, y, x + thumb_w, y + thumb_h], fill=(230, 230, 230))
        label = f"{_format_time(frame.time_seconds)}"
        if frame.skipped_reason:
            label += f" | {frame.skipped_reason}"
        draw.rectangle([x, y + thumb_h, x + thumb_w, y + thumb_h + label_h], fill=(20, 20, 20))
        draw.text((x + 8, y + thumb_h + 9), label, fill="white")
    canvas.save(output_path, quality=90)


def _record(video_file: str, path: Path, frames: list[ExtractedFrame]) -> Filmstrip:
    return Filmstrip(
        video_file=video_file,
        path=str(path),
        frame_paths=[frame.path for frame in frames],
        start_time=min((frame.time_seconds for frame in frames), default=0.0),
        end_time=max((frame.time_seconds for frame in frames), default=0.0),
    )


def _format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

