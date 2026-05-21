from __future__ import annotations

from collections import defaultdict

from vlog_script_generator.models import AsrSegment, MaterialAnalysis, VideoMetadata


def build_material_summary(
    metadata: list[VideoMetadata],
    analyses: list[MaterialAnalysis],
    asr: dict[str, list[AsrSegment]] | None = None,
) -> str:
    grouped: dict[str, list[MaterialAnalysis]] = defaultdict(list)
    for item in analyses:
        grouped[item.video_file].append(item)
    lines: list[str] = []
    for meta in metadata:
        lines.append(f"视频：{meta.file_name}，时长 {_fmt(meta.duration)}，分辨率 {meta.width}x{meta.height}，废片初筛：{meta.waste_reason or '未发现明显问题'}")
        for analysis in grouped.get(meta.file_name, []):
            lines.append(f"- 胶片流：{analysis.summary}；可用性：{analysis.waste_level}；情绪：{analysis.emotion}；建议：{analysis.editing_notes}")
        speech = asr.get(meta.file_name, []) if asr else []
        if speech:
            joined = " / ".join(seg.text for seg in speech[:5])
            lines.append(f"- 字幕摘要：{joined}")
    return "\n".join(lines)


def _fmt(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

