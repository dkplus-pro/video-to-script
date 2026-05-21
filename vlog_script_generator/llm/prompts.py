from __future__ import annotations

from pathlib import Path

from vlog_script_generator.core.config import read_yaml


DEFAULT_PROMPTS = {
    "vision_analyze_filmstrip": "你是一个中文 Vlog 视频素材分析助手，请分析胶片流。",
    "story_expand": "你是一个短视频编剧，请根据故事和素材扩写。",
    "script_table_writer": "请输出一个完整 Markdown 表格。",
}


def load_prompts(path: str | None = None) -> dict[str, str]:
    prompt_path = Path(path) if path else Path("config/prompts.yaml")
    prompts = dict(DEFAULT_PROMPTS)
    if prompt_path.exists():
        prompts.update(read_yaml(prompt_path))
    return prompts

