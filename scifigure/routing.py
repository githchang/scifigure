from __future__ import annotations

from collections import defaultdict

from .models import EdgeSpec, FigureIR, Rect, ResolvedEdge, ResolvedFigure, ResolvedNode
from .style import edge_style


def _primary_nodes(fig: ResolvedFigure) -> dict[str, ResolvedNode]:
    result: dict[str, ResolvedNode] = {}
    for node in fig.nodes:
        if node.instance_role == "primary" and node.source_id not in result:
            result[node.source_id] = node
    for node in fig.nodes:
        result.setdefault(node.source_id, node)
    return result


def _port(rect: Rect, toward: Rect) -> tuple[tuple[float, float], str]:
    dx = toward.cx - rect.cx
    dy = toward.cy - rect.cy
    if abs(dx) >= abs(dy):
        if dx >= 0:
            return (rect.right, rect.cy), "right"
        return (rect.left, rect.cy), "left"
    if dy >= 0:
        return (rect.cx, rect.bottom), "bottom"
    return (rect.cx, rect.top), "top"


def _orthogonal_points(src: Rect, dst: Rect, offset: float = 0.0) -> list[tuple[float, float]]:
    start, sside = _port(src, dst)
    end, eside = _port(dst, src)
    sx, sy = start
    ex, ey = end
    if sside in {"right", "left"} and eside in {"right", "left"}:
        midx = (sx + ex) / 2 + offset
        return [(sx, sy), (midx, sy), (midx, ey), (ex, ey)]
    if sside in {"top", "bottom"} and eside in {"top", "bottom"}:
        midy = (sy + ey) / 2 + offset
        return [(sx, sy), (sx, midy), (ex, midy), (ex, ey)]
    if sside in {"right", "left"}:
        return [(sx, sy), (ex, sy), (ex, ey)]
    return [(sx, sy), (sx, ey), (ex, ey)]


def _straight_points(src: Rect, dst: Rect) -> list[tuple[float, float]]:
    start, _ = _port(src, dst)
    end, _ = _port(dst, src)
    return [start, end]


def _feedback_points(src: Rect, dst: Rect, canvas_h: float, index: int) -> list[tuple[float, float]]:
    start, _ = _port(src, dst)
    end, _ = _port(dst, src)
    y = min(canvas_h - 26, max(src.bottom, dst.bottom) + 34 + index * 12)
    return [start, (start[0], y), (end[0], y), end]


def route_edges(ir: FigureIR, fig: ResolvedFigure, style: dict) -> ResolvedFigure:
    nodes = _primary_nodes(fig)
    pair_counts: dict[tuple[str, str], int] = defaultdict(int)
    resolved: list[ResolvedEdge] = []
    for i, edge in enumerate(ir.edges):
        src = nodes.get(edge.source)
        dst = nodes.get(edge.target)
        if src is None or dst is None:
            continue
        pair = (edge.source, edge.target)
        offset_index = pair_counts[pair]
        pair_counts[pair] += 1
        offset = (offset_index - 0.5 * max(0, pair_counts[pair] - 1)) * 10
        etype = edge.type or "data_flow"
        if etype == "feedback":
            points = _feedback_points(src.rect, dst.rect, fig.canvas.height, offset_index)
        elif style.get("layout") == "rigorous_graph" and etype not in {"residual", "skip", "feedback"}:
            points = _straight_points(src.rect, dst.rect)
        else:
            points = _orthogonal_points(src.rect, dst.rect, offset)
        es = edge_style(style, etype)
        resolved.append(ResolvedEdge(
            id=f"e{i+1}-{edge.source}-{edge.target}",
            source=src.id,
            target=dst.id,
            type=etype,
            points=points,
            color=es.get("color", "#4B5563"),
            width=float(es.get("width", 2.0)),
            dashed=bool(es.get("dashed", False)),
            arrow="end",
            label=edge.label,
            locked=edge.locked,
            metadata=dict(edge.metadata),
        ))
    fig.edges = resolved
    return fig
