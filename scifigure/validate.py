from __future__ import annotations

import math
from dataclasses import asdict
from typing import Any

from .models import FigureIR, Rect, ResolvedEdge, ResolvedFigure


class ValidationError(ValueError):
    pass


def validate_ir(ir: FigureIR) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    ids = [n.id for n in ir.nodes]
    if not ir.title.strip():
        errors.append("title must not be empty")
    if not ir.nodes:
        errors.append("at least one node is required")
    duplicates = sorted({x for x in ids if ids.count(x) > 1})
    if duplicates:
        errors.append(f"duplicate node ids: {duplicates}")
    idset = set(ids)
    group_ids = {g.id for g in ir.groups}
    if len(group_ids) != len(ir.groups):
        errors.append("duplicate group ids")
    for n in ir.nodes:
        if not n.label.strip():
            errors.append(f"node {n.id}: label must not be empty")
        if n.group and group_ids and n.group not in group_ids:
            errors.append(f"node {n.id}: unknown group {n.group}")
    for i, e in enumerate(ir.edges):
        if e.source not in idset:
            errors.append(f"edge {i}: unknown source {e.source}")
        if e.target not in idset:
            errors.append(f"edge {i}: unknown target {e.target}")
        if e.source == e.target and e.type != "feedback":
            warnings.append(f"edge {i}: self-loop is normally reserved for feedback")
    if ir.canvas.width < 800 or ir.canvas.height < 450:
        warnings.append("canvas is smaller than the recommended 800x450")
    if errors:
        raise ValidationError("; ".join(errors))
    return {"valid": True, "errors": errors, "warnings": warnings, "node_count": len(ir.nodes), "edge_count": len(ir.edges)}


def _overlap(a: Rect, b: Rect, pad: float = 2.0) -> bool:
    return not (a.right + pad <= b.left or b.right + pad <= a.left or a.bottom + pad <= b.top or b.bottom + pad <= a.top)


def _point_in_rect(p: tuple[float, float], r: Rect, pad: float = 0.0) -> bool:
    return r.left - pad <= p[0] <= r.right + pad and r.top - pad <= p[1] <= r.bottom + pad


def _segments(points: list[tuple[float, float]]):
    for a, b in zip(points, points[1:]):
        yield a, b


def _segment_hits_rect(a: tuple[float, float], b: tuple[float, float], r: Rect) -> bool:
    # Fast check for orthogonal and straight segments using sampling plus bounding boxes.
    minx, maxx = sorted((a[0], b[0]))
    miny, maxy = sorted((a[1], b[1]))
    if maxx < r.left or minx > r.right or maxy < r.top or miny > r.bottom:
        return False
    steps = max(3, int(max(abs(b[0]-a[0]), abs(b[1]-a[1])) / 8))
    for i in range(1, steps):
        t = i / steps
        p = (a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t)
        if _point_in_rect(p, r, 1):
            return True
    return False


def _orientation(a, b, c) -> float:
    return (b[1]-a[1])*(c[0]-b[0]) - (b[0]-a[0])*(c[1]-b[1])


def _intersect(a,b,c,d) -> bool:
    o1=_orientation(a,b,c); o2=_orientation(a,b,d); o3=_orientation(c,d,a); o4=_orientation(c,d,b)
    return (o1*o2 < 0) and (o3*o4 < 0)


def validate_geometry(fig: ResolvedFigure) -> dict[str, Any]:
    warnings: list[dict[str, Any]] = []
    W,H=fig.canvas.width,fig.canvas.height
    for n in fig.nodes:
        r=n.rect
        if r.left < 0 or r.top < 0 or r.right > W or r.bottom > H:
            warnings.append({"type":"out_of_bounds","node":n.id})
        max_chars=max(8,int(r.width/(n.font_size*0.52)))
        estimated_lines=math.ceil(len(n.label)/max_chars)+min(3,len(n.details))+(1 if n.dimension else 0)
        available=max(1,int((r.height-20)/(n.font_size*1.22)))
        if estimated_lines > available:
            warnings.append({"type":"text_overflow_risk","node":n.id,"estimated_lines":estimated_lines,"available_lines":available})
    primary=[n for n in fig.nodes if n.instance_role=='primary']
    for i,a in enumerate(primary):
        for b in primary[i+1:]:
            if _overlap(a.rect,b.rect):
                warnings.append({"type":"node_overlap","nodes":[a.id,b.id]})
    node_by_id={n.id:n for n in fig.nodes}
    for e in fig.edges:
        for n in primary:
            if n.id in {e.source,e.target}:
                continue
            if any(_segment_hits_rect(a,b,n.rect.expanded(2)) for a,b in _segments(e.points)):
                warnings.append({"type":"edge_through_node","edge":e.id,"node":n.id})
    for i,e1 in enumerate(fig.edges):
        for e2 in fig.edges[i+1:]:
            if {e1.source,e1.target} & {e2.source,e2.target}:
                continue
            crossed=False
            for a,b in _segments(e1.points):
                for c,d in _segments(e2.points):
                    if _intersect(a,b,c,d): crossed=True; break
                if crossed: break
            if crossed:
                warnings.append({"type":"edge_crossing","edges":[e1.id,e2.id]})
    return {"valid": not any(w["type"] in {"node_overlap","out_of_bounds"} for w in warnings), "warnings": warnings, "counts": {"nodes":len(fig.nodes),"edges":len(fig.edges),"groups":len(fig.groups)}}
