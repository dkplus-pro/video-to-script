from __future__ import annotations

import json
from pathlib import Path

from vlog_script_generator.llm.client import OpenAICompatibleClient
from vlog_script_generator.models import Filmstrip, MaterialAnalysis
from vlog_script_generator.storage.cache import write_json


def _vision_config(config: dict) -> dict:
    llm = config.get("llm", {})
    return {**llm, **llm.get("vision", {})}


def analyze_filmstrip(
    filmstrip: Filmstrip,
    output_root: str | Path,
    config: dict,
    prompts: dict[str, str],
    force: bool = False,
) -> MaterialAnalysis:
    out_dir = Path(output_root) / Path(filmstrip.video_file).stem
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{Path(filmstrip.path).stem}.json"
    if out_path.exists() and not force:
        data = json.loads(out_path.read_text(encoding="utf-8"))
        return MaterialAnalysis(**data)

    cfg = _vision_config(config)
    client = OpenAICompatibleClient(cfg, shared=config.get("llm", {}))
    if client.enabled and cfg.get("model"):
        analysis = _analyze_with_llm(client, filmstrip, prompts)
    else:
        analysis = _heuristic_analysis(filmstrip)
    write_json(out_path, analysis.to_dict())
    return analysis


def _analyze_with_llm(client: OpenAICompatibleClient, filmstrip: Filmstrip, prompts: dict[str, str]) -> MaterialAnalysis:
    content = [
        {"type": "text", "text": prompts.get("vision_analyze_filmstrip", "")},
        {"type": "image_url", "image_url": {"url": client.image_to_data_url(filmstrip.path)}},
    ]
    text = client.chat([{"role": "user", "content": content}], model=client.model)
    try:
        data = json.loads(_strip_code_fence(text))
    except Exception:
        data = {"summary": text}
    return MaterialAnalysis(
        video_file=filmstrip.video_file,
        filmstrip=filmstrip.path,
        summary=data.get("summary", text),
        usable_segments=data.get("usable_segments", []),
        waste_level=data.get("waste_level", "部分可用"),
        emotion=data.get("emotion", "未知"),
        editing_notes=data.get("editing_notes", ""),
    )


def _heuristic_analysis(filmstrip: Filmstrip) -> MaterialAnalysis:
    return MaterialAnalysis(
        video_file=filmstrip.video_file,
        filmstrip=filmstrip.path,
        summary=f"已生成 {len(filmstrip.frame_paths)} 个关键帧的胶片流，时间范围 {_fmt(filmstrip.start_time)}-{_fmt(filmstrip.end_time)}。未配置视觉模型，画面内容需人工复核。",
        usable_segments=[{"start": filmstrip.start_time, "end": filmstrip.end_time, "reason": "通过本地抽帧保留，可作为候选素材"}],
        waste_level="部分可用",
        emotion="待判断",
        editing_notes="建议人工查看胶片流后确认镜头内容；配置视觉模型后可自动生成更细的画面描述。",
    )


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def _fmt(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

