from __future__ import annotations

from vlog_script_generator.llm.client import OpenAICompatibleClient
from vlog_script_generator.output.markdown_writer import rows_to_markdown


def generate_script_with_llm(story: str, material_summary: str, config: dict, prompts: dict[str, str]) -> str | None:
    client = OpenAICompatibleClient(config)
    if not client.enabled or not config.get("llm", {}).get("textModel"):
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
    return client.chat([{"role": "user", "content": prompt}], model=config.get("llm", {}).get("textModel"))


def generate_fallback_script(rows: list[dict[str, str]]) -> str:
    return rows_to_markdown(rows)

