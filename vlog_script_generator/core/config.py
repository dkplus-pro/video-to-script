from __future__ import annotations

import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


DEFAULT_CONFIG = {
    "app": {"outputDirName": ".output"},
    "video": {"extensions": ["mp4", "mov", "mkv", "avi", "m4v"], "maxWorkers": 2},
    "frames": {
        "minFrames": 6,
        "maxFrames": 24,
        "framesPerFilmstrip": 9,
        "jpegQuality": 88,
        "blackThreshold": 12,
        "blurThreshold": 45,
        "duplicateHashDistance": 4,
    },
    "audio": {"sampleRate": 16000, "asrProvider": "none", "whisperModel": "small"},
    "llm": {
        "temperature": 0.7,
        "maxTokens": 8000,
        "timeoutSeconds": 120,
        "enabled": False,
        "text": {
            "provider": "openai-compatible",
            "baseURL": "",
            "apiKey": "",
            "model": "",
        },
        "vision": {
            "provider": "openai-compatible",
            "baseURL": "",
            "apiKey": "",
            "model": "",
        },
    },
    "pipeline": {"retryTimes": 2, "resume": True},
}


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        pattern = re.compile(r"\$\{([^}]+)\}")
        return pattern.sub(lambda m: os.getenv(m.group(1), ""), value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if yaml is None:
        raise RuntimeError("PyYAML is required to read YAML config files.")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML config must be a mapping: {path}")
    return data


def _migrate_llm_config(llm: dict[str, Any]) -> None:
    flat_keys = {"baseURL", "apiKey", "textModel", "visionModel", "provider"}
    if not flat_keys.intersection(llm):
        return
    text = llm.setdefault("text", {})
    vision = llm.setdefault("vision", {})
    if "provider" in llm:
        text.setdefault("provider", llm["provider"])
        vision.setdefault("provider", llm["provider"])
    if "baseURL" in llm:
        text.setdefault("baseURL", llm["baseURL"])
        vision.setdefault("baseURL", llm["baseURL"])
    if "apiKey" in llm:
        text.setdefault("apiKey", llm["apiKey"])
        vision.setdefault("apiKey", llm["apiKey"])
    if llm.get("textModel"):
        text.setdefault("model", llm["textModel"])
    if llm.get("visionModel"):
        vision.setdefault("model", llm["visionModel"])
    for key in flat_keys:
        llm.pop(key, None)


def load_config(config_path: str | None = None) -> dict[str, Any]:
    project_default = Path("config/default.yaml")
    config = _merge(DEFAULT_CONFIG, read_yaml(project_default) if project_default.exists() else {})
    if config_path:
        config = _merge(config, read_yaml(Path(config_path)))
    config = _expand_env(config)
    llm = config.setdefault("llm", {})
    _migrate_llm_config(llm)
    text = llm.get("text", {})
    vision = llm.get("vision", {})
    llm["enabled"] = bool(
        llm.get("enabled")
        and (
            (text.get("baseURL") and text.get("apiKey"))
            or (vision.get("baseURL") and vision.get("apiKey"))
        )
    )
    return config

