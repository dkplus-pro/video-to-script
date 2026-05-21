from __future__ import annotations

from pathlib import Path

from vlog_script_generator.models import ensure_dir


SCRIPT_COLUMNS = [
    "序号",
    "故事段落",
    "脚本内容",
    "素材来源视频",
    "素材时间范围",
    "画面内容描述",
    "使用原因",
    "建议剪辑方式",
    "建议音效",
    "建议 BGM 情绪",
    "建议花字",
    "是否需要旁白",
    "旁白内容",
    "备注",
]


def rows_to_markdown(rows: list[dict[str, str]]) -> str:
    header = "| " + " | ".join(SCRIPT_COLUMNS) + " |"
    sep = "| " + " | ".join("---" for _ in SCRIPT_COLUMNS) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(_clean(row.get(col, "")) for col in SCRIPT_COLUMNS) + " |")
    return "\n".join([header, sep, *body]) + "\n"


def write_markdown(path: str | Path, content: str) -> Path:
    target = Path(path)
    ensure_dir(target.parent)
    target.write_text(content, encoding="utf-8")
    return target


def _clean(value: object) -> str:
    text = str(value).replace("\n", "<br>").replace("|", "\\|")
    return text.strip()

