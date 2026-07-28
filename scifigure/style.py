from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

STYLE_IDS = [
    "s1-compact-modular",
    "s2-multi-panel",
    "s3-dense-engineering",
    "s4-macro-partition",
    "s5-rigorous-graph",
    "s6-paperbanana-soft",
]


def style_dir() -> Path:
    return Path(str(files("scifigure").joinpath("style_packs")))


def load_style(style_id: str) -> dict[str, Any]:
    if style_id not in STYLE_IDS:
        raise ValueError(f"Unknown style: {style_id}. Expected one of: {', '.join(STYLE_IDS)}")
    path = style_dir() / f"{style_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def all_styles() -> list[dict[str, Any]]:
    return [load_style(style_id) for style_id in STYLE_IDS]


def role_colors(style: dict[str, Any], role: str | None, node_type: str | None = None) -> tuple[str, str, str]:
    role = (role or "process").lower()
    node_type = (node_type or "process").lower()
    semantic = style["semantic_colors"]
    key = role if role in semantic else node_type if node_type in semantic else "process"
    entry = semantic.get(key, semantic["process"])
    return entry["fill"], entry["stroke"], entry.get("text", style["text_primary"])


def edge_style(style: dict[str, Any], edge_type: str) -> dict[str, Any]:
    return dict(style["edge_styles"].get(edge_type, style["edge_styles"]["data_flow"]))
