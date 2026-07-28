from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CanvasSpec:
    width: int = 1600
    height: int = 900
    background: str = "#FFFFFF"
    margin: int = 48


@dataclass(slots=True)
class NodeSpec:
    id: str
    label: str
    type: str = "process"
    group: str | None = None
    role: str | None = None
    details: list[str] = field(default_factory=list)
    dimension: str | None = None
    note: str | None = None
    locked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EdgeSpec:
    source: str
    target: str
    type: str = "data_flow"
    label: str | None = None
    locked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GroupSpec:
    id: str
    label: str
    role: str = "process"
    note: str | None = None
    locked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AnnotationSpec:
    id: str
    text: str
    target: str | None = None
    kind: str = "note"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FigureIR:
    title: str
    subtitle: str | None = None
    figure_type: str = "methodology_diagram"
    reading_direction: str = "left_to_right"
    canvas: CanvasSpec = field(default_factory=CanvasSpec)
    nodes: list[NodeSpec] = field(default_factory=list)
    edges: list[EdgeSpec] = field(default_factory=list)
    groups: list[GroupSpec] = field(default_factory=list)
    annotations: list[AnnotationSpec] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Rect:
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def cx(self) -> float:
        return self.x + self.width / 2

    @property
    def cy(self) -> float:
        return self.y + self.height / 2

    def expanded(self, pad: float) -> "Rect":
        return Rect(self.x - pad, self.y - pad, self.width + 2 * pad, self.height + 2 * pad)


@dataclass(slots=True)
class ResolvedGroup:
    id: str
    label: str
    role: str
    rect: Rect
    fill: str
    stroke: str
    dashed: bool = False
    title_fill: str | None = None
    order: int = 0


@dataclass(slots=True)
class ResolvedNode:
    id: str
    source_id: str
    label: str
    type: str
    role: str | None
    group: str | None
    rect: Rect
    fill: str
    stroke: str
    text_color: str
    border_width: float = 1.6
    radius: float = 12
    font_size: float = 18
    font_weight: int = 600
    details: list[str] = field(default_factory=list)
    dimension: str | None = None
    note: str | None = None
    instance_role: str = "primary"
    locked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResolvedEdge:
    id: str
    source: str
    target: str
    type: str
    points: list[tuple[float, float]]
    color: str
    width: float = 2.0
    dashed: bool = False
    arrow: str = "end"
    label: str | None = None
    locked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResolvedAnnotation:
    id: str
    text: str
    rect: Rect
    kind: str
    fill: str = "#FFFFFF"
    stroke: str = "#CBD5E1"
    text_color: str = "#334155"
    font_size: float = 14


@dataclass(slots=True)
class ResolvedFigure:
    title: str
    subtitle: str | None
    style_id: str
    canvas: CanvasSpec
    groups: list[ResolvedGroup]
    nodes: list[ResolvedNode]
    edges: list[ResolvedEdge]
    annotations: list[ResolvedAnnotation]
    legend: list[tuple[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
