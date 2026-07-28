from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import (
    AnnotationSpec,
    CanvasSpec,
    EdgeSpec,
    FigureIR,
    GroupSpec,
    NodeSpec,
    Rect,
    ResolvedAnnotation,
    ResolvedEdge,
    ResolvedFigure,
    ResolvedGroup,
    ResolvedNode,
)


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_figure_ir(path: str | Path) -> FigureIR:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    canvas_raw = data.get("canvas") or {}
    canvas = CanvasSpec(
        width=int(canvas_raw.get("width", 1600)),
        height=int(canvas_raw.get("height", 900)),
        background=str(canvas_raw.get("background", "#FFFFFF")),
        margin=int(canvas_raw.get("margin", 48)),
    )
    nodes = [
        NodeSpec(
            id=str(n["id"]),
            label=str(n.get("label", n["id"])),
            type=str(n.get("type", "process")),
            group=n.get("group"),
            role=n.get("role"),
            details=[str(x) for x in _list(n.get("details"))],
            dimension=n.get("dimension"),
            note=n.get("note"),
            locked=bool(n.get("locked", False)),
            metadata=dict(n.get("metadata") or {}),
        )
        for n in _list(data.get("nodes"))
    ]
    edges = [
        EdgeSpec(
            source=str(e["source"]),
            target=str(e["target"]),
            type=str(e.get("type", "data_flow")),
            label=e.get("label"),
            locked=bool(e.get("locked", False)),
            metadata=dict(e.get("metadata") or {}),
        )
        for e in _list(data.get("edges"))
    ]
    groups = [
        GroupSpec(
            id=str(g["id"]),
            label=str(g.get("label", g["id"])),
            role=str(g.get("role", "process")),
            note=g.get("note"),
            locked=bool(g.get("locked", False)),
            metadata=dict(g.get("metadata") or {}),
        )
        for g in _list(data.get("groups"))
    ]
    annotations = [
        AnnotationSpec(
            id=str(a["id"]),
            text=str(a.get("text", "")),
            target=a.get("target"),
            kind=str(a.get("kind", "note")),
            metadata=dict(a.get("metadata") or {}),
        )
        for a in _list(data.get("annotations"))
    ]
    return FigureIR(
        title=str(data.get("title", "Scientific Figure")),
        subtitle=data.get("subtitle"),
        figure_type=str(data.get("figure_type", "methodology_diagram")),
        reading_direction=str(data.get("reading_direction", "left_to_right")),
        canvas=canvas,
        nodes=nodes,
        edges=edges,
        groups=groups,
        annotations=annotations,
        metadata=dict(data.get("metadata") or {}),
    )


def save_json(path: str | Path, data: Any) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(data, "__dataclass_fields__"):
        payload = asdict(data)
    else:
        payload = data
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _rect(d: dict[str, Any]) -> Rect:
    return Rect(float(d["x"]), float(d["y"]), float(d["width"]), float(d["height"]))


def load_resolved_figure(path: str | Path) -> ResolvedFigure:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    c = d["canvas"]
    canvas = CanvasSpec(int(c["width"]), int(c["height"]), c.get("background", "#FFFFFF"), int(c.get("margin", 48)))
    groups = [ResolvedGroup(rect=_rect(g.pop("rect")), **g) for g in [dict(x) for x in d.get("groups", [])]]
    nodes = [ResolvedNode(rect=_rect(n.pop("rect")), **n) for n in [dict(x) for x in d.get("nodes", [])]]
    edges = [ResolvedEdge(points=[tuple(p) for p in e.pop("points")], **e) for e in [dict(x) for x in d.get("edges", [])]]
    annotations = [ResolvedAnnotation(rect=_rect(a.pop("rect")), **a) for a in [dict(x) for x in d.get("annotations", [])]]
    return ResolvedFigure(
        title=d["title"], subtitle=d.get("subtitle"), style_id=d["style_id"], canvas=canvas,
        groups=groups, nodes=nodes, edges=edges, annotations=annotations,
        legend=[tuple(x) for x in d.get("legend", [])], metadata=dict(d.get("metadata") or {}),
    )
