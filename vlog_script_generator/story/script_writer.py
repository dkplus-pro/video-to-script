from __future__ import annotations

from pathlib import Path

from vlog_script_generator.llm.text_generator import generate_fallback_script, generate_script_with_llm
from vlog_script_generator.models import AsrSegment, MaterialAnalysis, VideoMetadata
from vlog_script_generator.story.material_indexer import build_material_summary


def generate_script(
    story_path: str | Path,
    metadata: list[VideoMetadata],
    analyses: list[MaterialAnalysis],
    asr: dict[str, list[AsrSegment]],
    config: dict,
    prompts: dict[str, str],
) -> str:
    story = Path(story_path).read_text(encoding="utf-8") if story_path else ""
    summary = build_material_summary(metadata, analyses, asr)
    llm_result = generate_script_with_llm(story, summary, config, prompts)
    if llm_result:
        return llm_result
    rows = _fallback_rows(story, metadata, analyses, asr)
    return generate_fallback_script(rows)


def _fallback_rows(
    story: str,
    metadata: list[VideoMetadata],
    analyses: list[MaterialAnalysis],
    asr: dict[str, list[AsrSegment]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    story_brief = story.strip().replace("\n", " ") or "根据素材整理 Vlog 故事"
    if not metadata:
        return [
            {
                "序号": "1",
                "故事段落": "素材缺失",
                "脚本内容": story_brief,
                "素材来源视频": "缺少画面",
                "素材时间范围": "",
                "画面内容描述": "未扫描到视频素材",
                "使用原因": "需要补充素材",
                "建议剪辑方式": "先补充可用视频",
                "建议音效": "",
                "建议 BGM 情绪": "待定",
                "建议花字": "缺少画面",
                "是否需要旁白": "需要",
                "旁白内容": story_brief,
                "备注": "未配置文本模型时使用模板输出",
            }
        ]
    analysis_by_video = {item.video_file: item for item in analyses}
    for index, meta in enumerate(metadata, start=1):
        analysis = analysis_by_video.get(meta.file_name)
        segments = asr.get(meta.file_name, [])
        subtitle = " ".join(seg.text for seg in segments[:2]).strip()
        start, end = _segment_range(analysis, meta)
        rows.append(
            {
                "序号": str(index),
                "故事段落": "候选素材" if index > 1 else "开场",
                "脚本内容": subtitle or f"围绕“{story_brief[:40]}”选用这一段画面，补充故事推进。",
                "素材来源视频": meta.file_name,
                "素材时间范围": f"{_fmt(start)}-{_fmt(end)}",
                "画面内容描述": analysis.summary if analysis else "已读取元信息，尚未生成视觉分析",
                "使用原因": "本地抽帧后保留为候选素材，可承接故事内容",
                "建议剪辑方式": "保留 3-8 秒有效片段，按故事节奏慢切或顺切",
                "建议音效": "环境声、脚步声或现场同期声",
                "建议 BGM 情绪": "生活感、温暖",
                "建议花字": "重点强调型花字",
                "是否需要旁白": "需要" if not subtitle else "可选",
                "旁白内容": "" if subtitle else story_brief,
                "备注": meta.waste_reason or (analysis.editing_notes if analysis else "建议接入视觉模型生成更准确描述"),
            }
        )
    return rows


def _segment_range(analysis: MaterialAnalysis | None, meta: VideoMetadata) -> tuple[float, float]:
    if analysis and analysis.usable_segments:
        item = analysis.usable_segments[0]
        return float(item.get("start", 0)), float(item.get("end", min(meta.duration, 8)))
    return 0.0, min(meta.duration, 8.0)


def _fmt(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

