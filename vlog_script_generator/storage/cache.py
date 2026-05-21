from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vlog_script_generator.models import ensure_dir


def read_json(path: str | Path, default: Any = None) -> Any:
    target = Path(path)
    if not target.exists():
        return default
    return json.loads(target.read_text(encoding="utf-8"))


def write_json(path: str | Path, data: Any) -> Path:
    target = Path(path)
    ensure_dir(target.parent)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return target

