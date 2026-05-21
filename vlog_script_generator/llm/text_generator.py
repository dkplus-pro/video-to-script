from __future__ import annotations

from vlog_script_generator.llm.client import OpenAICompatibleClient
from vlog_script_generator.output.markdown_writer import rows_to_markdown


def _text_config(config: dict) -> dict:
    llm = config.get("llm", {})
    return {**llm, **llm.get("text", {})}


def generate_script_with_llm(story: str, material_summary: str, config: dict, prompts: dict[str, str]) -> str | None:
    cfg = _text_config(config)
    client = OpenAICompatibleClient(cfg, shared=config.get("llm", {}))
    if not client.enabled or not cfg.get("model"):
        return None
    prompt = "\n\n".join(
        [
            prompts.get("story_expand", ""),
            prompts.get("script_table_writer", ""),
            "用户故事小结：",
            story,
            "素材摘要：",
            material_summary,
        ]
    )
    return client.chat([{"role": "user", "content": prompt}], model=cfg["model"])


def generate_fallback_script(rows: list[dict[str, str]]) -> str:
    return rows_to_markdown(rows)

