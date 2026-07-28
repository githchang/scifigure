from __future__ import annotations

import html
import math
import re
import textwrap
from pathlib import Path

from .models import Rect, ResolvedEdge, ResolvedFigure, ResolvedGroup, ResolvedNode


def _esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def _hex_id(color: str) -> str:
    return "m" + "".join(char for char in color if char.isalnum())


def _wrap(text: str, width_px: float, font_size: float, max_lines: int = 4) -> list[str]:
    if not text:
        return []
    chars = max(4, int(width_px / max(4.0, font_size * 0.55)))
    lines = textwrap.wrap(text, width=chars, break_long_words=False, break_on_hyphens=False) or [text]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if len(lines[-1]) > 2:
            lines[-1] = lines[-1][:-1] + "…"
    return lines


def _text(
    lines: list[str],
    x: float,
    y: float,
    *,
    font_size: float,
    fill: str,
    weight: int = 400,
    anchor: str = "middle",
    family: str = "Arial, sans-serif",
    line_height: float = 1.22,
    italic: bool = False,
    letter_spacing: float | None = None,
) -> str:
    if not lines:
        return ""
    tspans: list[str] = []
    for index, line in enumerate(lines):
        dy = "0" if index == 0 else f"{font_size * line_height:.2f}"
        tspans.append(f'<tspan x="{x:.2f}" dy="{dy}">{_esc(line)}</tspan>')
    style = "italic" if italic else "normal"
    spacing = "" if letter_spacing is None else f' letter-spacing="{letter_spacing:.2f}"'
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" '
        f'font-family="{_esc(family)}" font-size="{font_size:.2f}" font-weight="{weight}" '
        f'font-style="{style}" fill="{fill}"{spacing}>'
        + "".join(tspans)
        + "</text>"
    )


def _rounded_rect(
    rect: Rect,
    fill: str,
    stroke: str,
    width: float,
    radius: float,
    dashed: bool = False,
    opacity: float = 1.0,
    *,
    extra: str = "",
) -> str:
    dash = ' stroke-dasharray="8 6"' if dashed else ""
    return (
        f'<rect x="{rect.x:.2f}" y="{rect.y:.2f}" width="{rect.width:.2f}" height="{rect.height:.2f}" '
        f'rx="{radius:.2f}" fill="{fill}" fill-opacity="{opacity:.3f}" stroke="{stroke}" '
        f'stroke-width="{width:.2f}"{dash}{extra}/>'
    )


def _line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke: str,
    width: float = 1.0,
    dashed: bool = False,
) -> str:
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    return (
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{stroke}" stroke-width="{width:.2f}"{dash}/>'
    )


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    if len(value) != 6:
        return 128, 128, 128
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _mix(color: str, other: str = "#FFFFFF", ratio: float = 0.5) -> str:
    ratio = max(0.0, min(1.0, ratio))
    first = _hex_to_rgb(color)
    second = _hex_to_rgb(other)
    values = [round(first[index] * (1 - ratio) + second[index] * ratio) for index in range(3)]
    return "#" + "".join(f"{value:02X}" for value in values)


def _matrix_icon(rect: Rect, stroke: str, fill: str, *, rows: int = 4, columns: int = 4) -> str:
    size = min(rect.width, rect.height) * 0.72
    x = rect.cx - size / 2
    y = rect.cy - size / 2
    cell_width = size / columns
    cell_height = size / rows
    parts: list[str] = []
    for row in range(rows):
        for column in range(columns):
            opacity = 0.22 + 0.13 * ((row * 2 + column) % 4)
            parts.append(
                f'<rect x="{x + column * cell_width:.2f}" y="{y + row * cell_height:.2f}" '
                f'width="{max(1, cell_width - 1):.2f}" height="{max(1, cell_height - 1):.2f}" '
                f'fill="{fill}" fill-opacity="{opacity:.2f}" stroke="{stroke}" stroke-width="0.45"/>'
            )
    return "".join(parts)


def _tensor_icon(rect: Rect, stroke: str, fill: str) -> str:
    width = min(34, rect.width * 0.56)
    height = min(44, rect.height * 0.68)
    x = rect.cx - width / 2 - 6
    y = rect.cy - height / 2 + 5
    parts: list[str] = []
    for index in range(4):
        parts.append(
            f'<rect x="{x + index * 5:.2f}" y="{y - index * 4:.2f}" width="{width:.2f}" '
            f'height="{height:.2f}" rx="2" fill="{fill}" fill-opacity="{0.18 + index * 0.13:.2f}" '
            f'stroke="{stroke}" stroke-width="0.9"/>'
        )
    return "".join(parts)


def _cube_icon(rect: Rect, stroke: str, fill: str) -> str:
    size = min(rect.width, rect.height) * 0.55
    center_x, center_y = rect.cx, rect.cy
    depth_x, depth_y = size * 0.22, size * 0.16
    x0, y0 = center_x - size * 0.30, center_y - size * 0.23
    x1, y1 = x0 + size * 0.60, y0 + size * 0.46
    parts = [
        f'<polygon points="{x0:.2f},{y0:.2f} {x1:.2f},{y0:.2f} {x1:.2f},{y1:.2f} {x0:.2f},{y1:.2f}" '
        f'fill="{fill}" fill-opacity="0.28" stroke="{stroke}" stroke-width="0.9"/>',
        f'<polygon points="{x1:.2f},{y0:.2f} {x1 + depth_x:.2f},{y0 - depth_y:.2f} '
        f'{x1 + depth_x:.2f},{y1 - depth_y:.2f} {x1:.2f},{y1:.2f}" '
        f'fill="{fill}" fill-opacity="0.48" stroke="{stroke}" stroke-width="0.9"/>',
        f'<polygon points="{x0:.2f},{y0:.2f} {x0 + depth_x:.2f},{y0 - depth_y:.2f} '
        f'{x1 + depth_x:.2f},{y0 - depth_y:.2f} {x1:.2f},{y0:.2f}" '
        f'fill="{fill}" fill-opacity="0.38" stroke="{stroke}" stroke-width="0.9"/>',
    ]
    for fraction in (0.33, 0.66):
        x = x0 + size * 0.60 * fraction
        parts.append(_line(x, y0, x, y1, stroke, 0.45))
    return "".join(parts)


def _vector_icon(rect: Rect, stroke: str, fill: str) -> str:
    count = 6
    bar_width = max(3, min(7, rect.width / 11))
    gap = bar_width * 0.55
    total = count * bar_width + (count - 1) * gap
    x = rect.cx - total / 2
    y = rect.cy - rect.height * 0.28
    height = rect.height * 0.56
    parts: list[str] = []
    for index in range(count):
        parts.append(
            f'<rect x="{x + index * (bar_width + gap):.2f}" y="{y:.2f}" width="{bar_width:.2f}" '
            f'height="{height:.2f}" rx="1.5" fill="{fill}" fill-opacity="{0.20 + 0.10 * index:.2f}" '
            f'stroke="{stroke}" stroke-width="0.55"/>'
        )
    return "".join(parts)


def _graph_icon(rect: Rect, stroke: str, fill: str) -> str:
    center_x, center_y = rect.cx, rect.cy
    scale = min(rect.width, rect.height) * 0.32
    points = [
        (center_x - scale, center_y),
        (center_x - scale * 0.15, center_y - scale * 0.75),
        (center_x + scale, center_y - scale * 0.10),
        (center_x + scale * 0.35, center_y + scale * 0.78),
        (center_x - scale * 0.55, center_y + scale * 0.55),
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (1, 3), (0, 2)]
    parts = [_line(*points[source], *points[target], stroke, 0.9) for source, target in edges]
    for index, (x, y) in enumerate(points):
        parts.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{3.2 + index % 2:.2f}" fill="{fill}" '
            f'fill-opacity="{0.46 + 0.09 * (index % 3):.2f}" stroke="{stroke}" stroke-width="0.8"/>'
        )
    return "".join(parts)


def _document_icon(rect: Rect, stroke: str, fill: str) -> str:
    width = min(30, rect.width * 0.56)
    height = min(42, rect.height * 0.70)
    x, y = rect.cx - width / 2, rect.cy - height / 2
    fold = min(8, width * 0.25)
    return (
        f'<path d="M{x:.2f},{y:.2f} h{width - fold:.2f} l{fold:.2f},{fold:.2f} '
        f'v{height - fold:.2f} h-{width:.2f} z" fill="{fill}" fill-opacity="0.30" '
        f'stroke="{stroke}" stroke-width="0.9"/>'
        f'<path d="M{x + width - fold:.2f},{y:.2f} v{fold:.2f} h{fold:.2f}" '
        f'fill="none" stroke="{stroke}" stroke-width="0.9"/>'
        + _line(x + 6, y + height * 0.46, x + width - 6, y + height * 0.46, stroke, 0.7)
        + _line(x + 6, y + height * 0.64, x + width - 6, y + height * 0.64, stroke, 0.7)
    )


def _waveform_icon(rect: Rect, stroke: str, *, cycles: float = 2.5) -> str:
    x0 = rect.x + 4
    width = rect.width - 8
    amplitude = rect.height * 0.24
    points: list[str] = []
    samples = 28
    for index in range(samples + 1):
        x = x0 + width * index / samples
        phase = 2 * math.pi * cycles * index / samples
        y = rect.cy + math.sin(phase) * amplitude * (0.65 + 0.25 * math.sin(phase * 0.4))
        points.append(f"{x:.2f},{y:.2f}")
    return (
        f'<polyline points="{" ".join(points)}" fill="none" stroke="{stroke}" '
        f'stroke-width="1.15" stroke-linecap="round"/>'
    )


def _frequency_icon(rect: Rect, stroke: str, fill: str) -> str:
    parts = [_line(rect.x + 4, rect.bottom - 6, rect.right - 4, rect.bottom - 6, stroke, 0.7)]
    count = 9
    for index in range(count):
        x = rect.x + 7 + index * (rect.width - 14) / max(1, count - 1)
        height = rect.height * (0.18 + 0.55 * abs(math.sin(index * 0.78 + 0.4)))
        parts.append(
            f'<rect x="{x - 1.4:.2f}" y="{rect.bottom - 6 - height:.2f}" width="2.8" '
            f'height="{height:.2f}" fill="{fill}" fill-opacity="0.65" '
            f'stroke="{stroke}" stroke-width="0.35"/>'
        )
    return "".join(parts)


def _dot_row_icon(rect: Rect, stroke: str, fill: str) -> str:
    count = 7
    gap = rect.width / (count + 1)
    parts: list[str] = []
    for index in range(count):
        opacity = 0.35 + 0.08 * (index % 4)
        parts.append(
            f'<circle cx="{rect.x + gap * (index + 1):.2f}" cy="{rect.cy:.2f}" '
            f'r="{min(4.5, rect.height * 0.18):.2f}" fill="{fill}" fill-opacity="{opacity:.2f}" '
            f'stroke="{stroke}" stroke-width="0.6"/>'
        )
    return "".join(parts)


def _operator_icon(rect: Rect, stroke: str, text: str, *, fill: str = "#FFFFFF") -> str:
    radius = min(rect.width, rect.height) * 0.28
    return (
        f'<circle cx="{rect.cx:.2f}" cy="{rect.cy:.2f}" r="{radius:.2f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
        + _text(
            [text],
            rect.cx,
            rect.cy + radius * 0.34,
            font_size=radius * 1.05,
            fill=stroke,
            weight=700,
        )
    )


def _type_icon(node: ResolvedNode, area: Rect, *, style_id: str, palette: list[str]) -> str:
    node_type = node.type.lower()
    fill = palette[0] if palette else node.fill
    if node_type in {"matrix", "attention", "mask", "heatmap"}:
        return _matrix_icon(area, node.stroke, fill)
    if node_type in {"tensor", "embedding", "feature", "stack"}:
        return _cube_icon(area, node.stroke, fill) if style_id == "s3-dense-engineering" else _tensor_icon(area, node.stroke, fill)
    if node_type in {"vector", "score", "probability"}:
        return _dot_row_icon(area, node.stroke, fill) if style_id == "s2-multi-panel" else _vector_icon(area, node.stroke, fill)
    if node_type in {"graph", "gcn", "relation_graph", "network"}:
        return _graph_icon(area, node.stroke, fill)
    if node_type in {"document", "input", "data", "dataset", "text", "signal"}:
        return _waveform_icon(area, node.stroke) if node_type in {"data", "signal"} else _document_icon(area, node.stroke, fill)
    if node_type in {"encoder", "backbone", "projection"} and style_id == "s3-dense-engineering":
        return _frequency_icon(area, node.stroke, fill)
    return ""


def _node_text(
    node: ResolvedNode,
    family: str,
    *,
    x: float,
    y: float,
    width: float,
    label_size: float | None = None,
    max_label_lines: int = 2,
    detail_size: float | None = None,
    max_details: int = 2,
    anchor: str = "middle",
) -> str:
    label_size = float(label_size or node.font_size)
    detail_size = float(detail_size or max(8.5, label_size - 2.5))
    label_lines = _wrap(node.label, width, label_size, max_lines=max_label_lines)
    parts = [
        _text(
            label_lines,
            x,
            y,
            font_size=label_size,
            fill=node.text_color,
            weight=node.font_weight,
            family=family,
            anchor=anchor,
        )
    ]
    current_y = y + max(1, len(label_lines)) * label_size * 1.18 + 2
    details: list[str] = []
    for detail in node.details[:max_details]:
        details.extend(_wrap(detail, width, detail_size, max_lines=1))
    if details:
        parts.append(
            _text(
                details,
                x,
                current_y,
                font_size=detail_size,
                fill=_mix(node.text_color, "#FFFFFF", 0.25),
                weight=400,
                family=family,
                line_height=1.12,
                anchor=anchor,
            )
        )
        current_y += len(details) * detail_size * 1.12 + 2
    if node.dimension:
        parts.append(
            _text(
                [node.dimension],
                x,
                current_y,
                font_size=max(8.2, detail_size - 0.4),
                fill=node.stroke,
                weight=600,
                family="DejaVu Sans Mono, monospace",
                italic=True,
                anchor=anchor,
            )
        )
    return "".join(parts)


def _node_s1(node: ResolvedNode, family: str, palette: list[str]) -> str:
    rect = node.rect
    parts = [f'<g id="node-{_esc(node.id)}">']
    parts.append(_rounded_rect(rect, "#FFFFFF", node.stroke, node.border_width, 4, opacity=0.98))
    parts.append(
        f'<rect x="{rect.x:.2f}" y="{rect.y:.2f}" width="{rect.width:.2f}" '
        f'height="4.5" rx="2" fill="{node.stroke}" fill-opacity="0.78"/>'
    )
    icon_area = Rect(rect.x + 8, rect.y + 12, min(36, rect.width * 0.24), rect.height - 22)
    icon = _type_icon(node, icon_area, style_id="s1-compact-modular", palette=palette)
    icon_width = icon_area.width + 6 if icon else 0
    parts.append(icon)
    text_x = rect.x + icon_width + (rect.width - icon_width) / 2
    parts.append(
        _node_text(
            node,
            family,
            x=text_x,
            y=rect.y + 27,
            width=rect.width - icon_width - 16,
            label_size=node.font_size,
            max_label_lines=2,
            max_details=1,
        )
    )
    parts.append("</g>")
    return "".join(parts)


def _node_s2(node: ResolvedNode, family: str, palette: list[str]) -> str:
    rect = node.rect
    parts = [f'<g id="node-{_esc(node.id)}">']
    parts.append(_rounded_rect(rect, node.fill, node.stroke, node.border_width, 9, opacity=0.96))
    header_height = min(20, rect.height * 0.25)
    parts.append(
        f'<path d="M{rect.x + 9:.2f},{rect.y:.2f} H{rect.right - 9:.2f} '
        f'Q{rect.right:.2f},{rect.y:.2f} {rect.right:.2f},{rect.y + 9:.2f} '
        f'V{rect.y + header_height:.2f} H{rect.x:.2f} V{rect.y + 9:.2f} '
        f'Q{rect.x:.2f},{rect.y:.2f} {rect.x + 9:.2f},{rect.y:.2f} Z" '
        f'fill="{node.stroke}" fill-opacity="0.14"/>'
    )
    parts.append(
        _text(
            _wrap(node.label, rect.width - 14, min(node.font_size, 11.5), max_lines=1),
            rect.cx,
            rect.y + header_height * 0.72,
            font_size=min(node.font_size, 11.5),
            fill=node.text_color,
            weight=700,
            family=family,
        )
    )
    icon_rect = Rect(rect.x + 10, rect.y + header_height + 5, rect.width - 20, max(18, rect.height - header_height - 12))
    if node.type.lower() in {"probability", "score", "output"}:
        parts.append(_dot_row_icon(icon_rect, node.stroke, palette[0] if palette else node.fill))
    elif node.type.lower() in {"data", "signal"}:
        parts.append(_waveform_icon(icon_rect, node.stroke, cycles=3.2))
    else:
        small_icon = Rect(icon_rect.x, icon_rect.y, min(38, icon_rect.width * 0.25), icon_rect.height)
        parts.append(_type_icon(node, small_icon, style_id="s2-multi-panel", palette=palette))
        if node.details:
            parts.append(
                _text(
                    _wrap(node.details[0], icon_rect.width - small_icon.width - 8, 8.8, max_lines=2),
                    small_icon.right + 5,
                    icon_rect.y + 13,
                    font_size=8.8,
                    fill=node.text_color,
                    weight=400,
                    family=family,
                    anchor="start",
                    line_height=1.10,
                )
            )
    parts.append("</g>")
    return "".join(parts)


def _node_s3(node: ResolvedNode, family: str, palette: list[str]) -> str:
    rect = node.rect
    parts = [f'<g id="node-{_esc(node.id)}">']
    parts.append(_rounded_rect(rect, node.fill, node.stroke, node.border_width, 1.5, opacity=0.97))
    top_band = min(17, rect.height * 0.22)
    parts.append(
        f'<rect x="{rect.x:.2f}" y="{rect.y:.2f}" width="{rect.width:.2f}" '
        f'height="{top_band:.2f}" fill="{node.stroke}" fill-opacity="0.17"/>'
    )
    stage_index = node.metadata.get("stage_index")
    if stage_index:
        badge_radius = min(10, rect.height * 0.13)
        parts.append(
            f'<circle cx="{rect.x + badge_radius + 4:.2f}" cy="{rect.y + top_band / 2:.2f}" '
            f'r="{badge_radius:.2f}" fill="#FFFFFF" stroke="{node.stroke}" stroke-width="0.9"/>'
        )
        parts.append(
            _text(
                [str(stage_index)],
                rect.x + badge_radius + 4,
                rect.y + top_band / 2 + badge_radius * 0.33,
                font_size=max(7.5, badge_radius * 0.9),
                fill=node.stroke,
                weight=700,
                family=family,
            )
        )
    title_x = rect.cx + (8 if stage_index else 0)
    parts.append(
        _text(
            _wrap(node.label, rect.width - 30, min(node.font_size, 10.8), max_lines=1),
            title_x,
            rect.y + top_band * 0.72,
            font_size=min(node.font_size, 10.8),
            fill=node.text_color,
            weight=700,
            family=family,
        )
    )
    icon_rect = Rect(rect.x + 8, rect.y + top_band + 7, min(48, rect.width * 0.35), rect.height - top_band - 14)
    parts.append(_type_icon(node, icon_rect, style_id="s3-dense-engineering", palette=palette))
    text_x = icon_rect.right + 5
    text_width = rect.right - text_x - 6
    if text_width > 20:
        if node.details:
            parts.append(
                _text(
                    _wrap(node.details[0], text_width, 8.2, max_lines=2),
                    text_x,
                    rect.y + top_band + 17,
                    font_size=8.2,
                    fill=node.text_color,
                    weight=400,
                    family=family,
                    anchor="start",
                    line_height=1.1,
                )
            )
        if node.dimension:
            parts.append(
                _text(
                    _wrap(node.dimension, text_width, 7.8, max_lines=1),
                    text_x,
                    rect.bottom - 8,
                    font_size=7.8,
                    fill=node.stroke,
                    weight=600,
                    family="DejaVu Sans Mono, monospace",
                    anchor="start",
                    italic=True,
                )
            )
    parts.append("</g>")
    return "".join(parts)


def _node_s4(node: ResolvedNode, family: str, palette: list[str]) -> str:
    rect = node.rect
    parts = [f'<g id="node-{_esc(node.id)}" filter="url(#softShadow)">']
    parts.append(_rounded_rect(rect, node.fill, node.stroke, node.border_width, 3, opacity=0.96))
    accent_width = min(6, rect.width * 0.04)
    parts.append(
        f'<rect x="{rect.x:.2f}" y="{rect.y:.2f}" width="{accent_width:.2f}" '
        f'height="{rect.height:.2f}" fill="{node.stroke}" fill-opacity="0.65"/>'
    )
    icon_rect = Rect(rect.x + 11, rect.y + 9, min(46, rect.width * 0.28), rect.height - 18)
    if node.metadata.get("lane_key") == "input":
        parts.append(_waveform_icon(icon_rect, node.stroke, cycles=2.7))
    elif node.type.lower() in {"attention", "mask", "matrix", "heatmap"}:
        parts.append(_matrix_icon(icon_rect, node.stroke, palette[0] if palette else node.fill, rows=5, columns=5))
    else:
        parts.append(_type_icon(node, icon_rect, style_id="s4-macro-partition", palette=palette))
    icon_width = icon_rect.width + 5
    parts.append(
        _node_text(
            node,
            family,
            x=rect.x + icon_width + (rect.width - icon_width) / 2,
            y=rect.y + 24,
            width=rect.width - icon_width - 12,
            label_size=node.font_size,
            max_label_lines=2,
            max_details=1,
        )
    )
    parts.append("</g>")
    return "".join(parts)


def _node_s5(node: ResolvedNode, family: str, palette: list[str]) -> str:
    rect = node.rect
    parts = [f'<g id="node-{_esc(node.id)}">']
    if node.metadata.get("alignment_band"):
        parts.append(_rounded_rect(rect, node.fill, node.stroke, 1.5, 5, opacity=0.98))
        parts.append(
            f'<rect x="{rect.x + 4:.2f}" y="{rect.y + 4:.2f}" width="{rect.width - 8:.2f}" '
            f'height="{rect.height - 8:.2f}" rx="3" fill="none" stroke="{node.stroke}" '
            f'stroke-opacity="0.35" stroke-width="0.8"/>'
        )
        for fraction in (0.18, 0.50, 0.82):
            x = rect.x + rect.width * fraction
            parts.append(
                f'<circle cx="{x:.2f}" cy="{rect.y:.2f}" r="3.2" fill="#FFFFFF" '
                f'stroke="{node.stroke}" stroke-width="0.8"/>'
            )
            parts.append(
                f'<circle cx="{x:.2f}" cy="{rect.bottom:.2f}" r="3.2" fill="#FFFFFF" '
                f'stroke="{node.stroke}" stroke-width="0.8"/>'
            )
        parts.append(
            _text(
                _wrap(node.label, rect.width - 40, node.font_size, max_lines=1),
                rect.cx,
                rect.cy + node.font_size * 0.30,
                font_size=node.font_size,
                fill=node.text_color,
                weight=700,
                family=family,
            )
        )
        parts.append("</g>")
        return "".join(parts)
    parts.append(_rounded_rect(rect, node.fill, node.stroke, node.border_width, 7, opacity=0.97))
    parts.append(
        f'<rect x="{rect.x + 7:.2f}" y="{rect.y + 7:.2f}" width="{rect.width - 14:.2f}" '
        f'height="{min(19, rect.height * 0.22):.2f}" rx="3" '
        f'fill="{_mix(node.fill, node.stroke, 0.12)}" stroke="{node.stroke}" '
        f'stroke-opacity="0.35" stroke-width="0.6"/>'
    )
    parts.append(
        _text(
            _wrap(node.label, rect.width - 20, min(node.font_size, 11.5), max_lines=1),
            rect.cx,
            rect.y + 20,
            font_size=min(node.font_size, 11.5),
            fill=node.text_color,
            weight=700,
            family=family,
        )
    )
    inner_y = rect.y + 31
    row_height = max(15, (rect.height - 39) / 2)
    parts.append(
        f'<rect x="{rect.x + 9:.2f}" y="{inner_y:.2f}" width="{rect.width - 18:.2f}" '
        f'height="{row_height:.2f}" rx="2" fill="#FFFFFF" fill-opacity="0.50" '
        f'stroke="{node.stroke}" stroke-opacity="0.28" stroke-width="0.5"/>'
    )
    if node.details:
        parts.append(
            _text(
                _wrap(node.details[0], rect.width - 28, 8.8, max_lines=1),
                rect.cx,
                inner_y + row_height * 0.65,
                font_size=8.8,
                fill=node.text_color,
                weight=400,
                family=family,
            )
        )
    lower_y = inner_y + row_height + 4
    parts.append(
        f'<rect x="{rect.x + 9:.2f}" y="{lower_y:.2f}" width="{rect.width - 18:.2f}" '
        f'height="{max(10, rect.bottom - lower_y - 8):.2f}" rx="2" fill="{node.stroke}" '
        f'fill-opacity="0.08" stroke="{node.stroke}" stroke-opacity="0.22" stroke-width="0.5"/>'
    )
    if node.dimension:
        parts.append(
            _text(
                [node.dimension],
                rect.cx,
                rect.bottom - 12,
                font_size=8.3,
                fill=node.stroke,
                weight=600,
                family="DejaVu Sans Mono, monospace",
                italic=True,
            )
        )
    if node.metadata.get("gate_index"):
        gate_x = rect.right - 13
        gate_y = rect.y + 13
        parts.append(
            f'<circle cx="{gate_x:.2f}" cy="{gate_y:.2f}" r="6.2" '
            f'fill="#FFFFFF" stroke="{node.stroke}" stroke-width="0.8"/>'
        )
        parts.append(_text(["σ"], gate_x, gate_y + 2.7, font_size=7.5, fill=node.stroke, weight=700, family=family))
    parts.append("</g>")
    return "".join(parts)


def _node_s6(node: ResolvedNode, family: str, palette: list[str]) -> str:
    rect = node.rect
    parts = [f'<g id="node-{_esc(node.id)}">']
    parts.append(_rounded_rect(rect, node.fill, node.stroke, node.border_width, 4, opacity=0.92))
    sequence_index = node.metadata.get("sequence_index")
    if sequence_index:
        pill = Rect(rect.x + 8, rect.y + 8, 22, 16)
        parts.append(_rounded_rect(pill, "#FFFFFF", node.stroke, 0.7, 8, opacity=0.82))
        parts.append(_text([str(sequence_index)], pill.cx, pill.y + 11.2, font_size=8.2, fill=node.stroke, weight=700, family=family))
    parts.append(
        _text(
            _wrap(node.label, rect.width - 30, node.font_size, max_lines=2),
            rect.cx,
            rect.y + 28,
            font_size=node.font_size,
            fill=node.text_color,
            weight=700,
            family=family,
        )
    )
    separator_y = rect.y + min(42, rect.height * 0.45)
    parts.append(_line(rect.x + 12, separator_y, rect.right - 12, separator_y, node.stroke, 0.55))
    if node.details:
        parts.append(
            _text(
                _wrap(node.details[0], rect.width - 24, max(8.8, node.font_size - 2.3), max_lines=2),
                rect.cx,
                separator_y + 15,
                font_size=max(8.8, node.font_size - 2.3),
                fill=_mix(node.text_color, "#FFFFFF", 0.24),
                weight=400,
                family=family,
                line_height=1.12,
            )
        )
    elif node.type.lower() in {"probability", "output"}:
        parts.append(
            _dot_row_icon(
                Rect(rect.x + 16, separator_y + 6, rect.width - 32, rect.bottom - separator_y - 12),
                node.stroke,
                palette[0] if palette else node.fill,
            )
        )
    if node.dimension:
        parts.append(
            _text(
                [node.dimension],
                rect.cx,
                rect.bottom - 10,
                font_size=8.3,
                fill=node.stroke,
                weight=600,
                family="DejaVu Sans Mono, monospace",
                italic=True,
            )
        )
    parts.append("</g>")
    return "".join(parts)


def _node_svg(node: ResolvedNode, family: str, style_id: str, palette: list[str]) -> str:
    node_type = node.type.lower()
    if node_type in {"operator", "add", "multiply", "gate"}:
        symbol = {"add": "+", "multiply": "×", "gate": "σ"}.get(
            node_type,
            node.metadata.get("symbol", "⊕"),
        )
        return f'<g id="node-{_esc(node.id)}">{_operator_icon(node.rect, node.stroke, str(symbol), fill=node.fill)}</g>'
    if style_id == "s1-compact-modular":
        return _node_s1(node, family, palette)
    if style_id == "s2-multi-panel":
        return _node_s2(node, family, palette)
    if style_id == "s3-dense-engineering":
        return _node_s3(node, family, palette)
    if style_id == "s4-macro-partition":
        return _node_s4(node, family, palette)
    if style_id == "s5-rigorous-graph":
        return _node_s5(node, family, palette)
    return _node_s6(node, family, palette)


def _stage_number(group_id: str, fallback: int) -> int:
    match = re.search(r"(\d+)$", group_id)
    return int(match.group(1)) if match else fallback


def _group_s1(group: ResolvedGroup, family: str, style: dict) -> str:
    parts = [_rounded_rect(group.rect, "#FFFFFF", group.stroke, 1.0, 5, dashed=True, opacity=0.22)]
    parts.append(
        _text(
            _wrap(group.label, group.rect.width - 24, 12.2, max_lines=1),
            group.rect.x + 12,
            group.rect.y + 20,
            font_size=12.2,
            fill=style["text_primary"],
            weight=700,
            anchor="start",
            family=family,
        )
    )
    return "".join(parts)


def _group_s2(group: ResolvedGroup, family: str, style: dict) -> str:
    opacity = float(style.get("group_fill_opacity", 0.18))
    parts = [_rounded_rect(group.rect, group.fill, group.stroke, 1.1, 8, dashed=False, opacity=opacity)]
    parts.append(
        f'<rect x="{group.rect.x:.2f}" y="{group.rect.y:.2f}" width="{group.rect.width:.2f}" '
        f'height="28" rx="8" fill="{group.stroke}" fill-opacity="0.10"/>'
    )
    parts.append(
        _text(
            _wrap(group.label, group.rect.width - 22, 12, max_lines=1),
            group.rect.x + 11,
            group.rect.y + 19,
            font_size=12,
            fill=style["text_primary"],
            weight=700,
            anchor="start",
            family=family,
        )
    )
    return "".join(parts)


def _group_s3(group: ResolvedGroup, family: str, style: dict, index: int) -> str:
    number = _stage_number(group.id, index + 1)
    parts = [_rounded_rect(group.rect, "#FFFFFF", group.stroke, 1.0, 1.5, dashed=True, opacity=0.12)]
    bracket_x = group.rect.x + 5
    bracket_color = "#4F7B4B" if number in {1, 5, 6} else group.stroke
    parts.append(_line(bracket_x, group.rect.y + 8, bracket_x, group.rect.bottom - 8, bracket_color, 1.8))
    parts.append(_line(bracket_x, group.rect.y + 8, bracket_x + 10, group.rect.y + 8, bracket_color, 1.8))
    parts.append(_line(bracket_x, group.rect.bottom - 8, bracket_x + 10, group.rect.bottom - 8, bracket_color, 1.8))
    badge_y = group.rect.y + 28
    parts.append(
        f'<circle cx="{group.rect.x + 20:.2f}" cy="{badge_y:.2f}" r="11" '
        f'fill="#FFFFFF" stroke="{bracket_color}" stroke-width="1.3"/>'
    )
    parts.append(_text([str(number)], group.rect.x + 20, badge_y + 3.7, font_size=10.5, fill=bracket_color, weight=700, family=family))
    parts.append(
        _text(
            _wrap(group.label, group.rect.width - 56, 11.5, max_lines=2),
            group.rect.x + 38,
            group.rect.y + 24,
            font_size=11.5,
            fill=style["text_primary"],
            weight=700,
            anchor="start",
            family=family,
            line_height=1.05,
        )
    )
    return "".join(parts)


def _group_s4(group: ResolvedGroup, family: str, style: dict) -> str:
    parts = [_rounded_rect(group.rect, "#FFFFFF", group.stroke, 1.25, 3, dashed=False, opacity=0.16)]
    tab_width = min(group.rect.width - 20, max(150, len(group.label) * 7.2 + 26))
    tab = Rect(group.rect.x + 10, group.rect.y + 8, tab_width, 25)
    parts.append(_rounded_rect(tab, _mix(group.stroke, "#FFFFFF", 0.82), group.stroke, 0.8, 3, opacity=0.96))
    parts.append(
        _text(
            _wrap(group.label, tab.width - 14, 11.5, max_lines=1),
            tab.x + 8,
            tab.y + 17,
            font_size=11.5,
            fill=style["text_primary"],
            weight=700,
            anchor="start",
            family=family,
        )
    )
    return "".join(parts)


def _group_s5(group: ResolvedGroup, family: str, style: dict) -> str:
    radius = 4 if group.id == "s5-alignment" else 8
    parts = [
        _rounded_rect(
            group.rect,
            group.fill,
            group.stroke,
            1.05,
            radius,
            dashed=group.dashed,
            opacity=float(style.get("group_fill_opacity", 0.08)),
        )
    ]
    if group.id == "s5-alignment":
        parts.append(_line(group.rect.x + 18, group.rect.cy, group.rect.right - 18, group.rect.cy, group.stroke, 0.7, dashed=True))
    title = Rect(
        group.rect.x + 12,
        group.rect.y + 10,
        min(group.rect.width - 24, max(120, len(group.label) * 7.4 + 24)),
        25,
    )
    parts.append(_rounded_rect(title, "#FFFFFF", group.stroke, 0.7, 5, opacity=0.86))
    parts.append(
        _text(
            _wrap(group.label, title.width - 14, 11.5, max_lines=1),
            title.x + 8,
            title.y + 17,
            font_size=11.5,
            fill=style["text_primary"],
            weight=700,
            anchor="start",
            family=family,
        )
    )
    return "".join(parts)


def _group_s6(group: ResolvedGroup, family: str, style: dict, index: int) -> str:
    parts = [
        _rounded_rect(
            group.rect,
            group.fill,
            group.stroke,
            1.0,
            10,
            dashed=False,
            opacity=float(style.get("group_fill_opacity", 0.16)),
        )
    ]
    icon_x = group.rect.x + 22
    icon_y = group.rect.y + 22
    if index == 0:
        parts.append(
            f'<circle cx="{icon_x:.2f}" cy="{icon_y:.2f}" r="8" '
            f'fill="#FFFFFF" stroke="{group.stroke}" stroke-width="0.8"/>'
        )
        parts.append(
            f'<path d="M{icon_x - 4:.2f},{icon_y:.2f} q4,-7 8,0 q-4,7 -8,0" '
            f'fill="none" stroke="{group.stroke}" stroke-width="0.8"/>'
        )
    elif index == 1:
        parts.append(
            f'<circle cx="{icon_x:.2f}" cy="{icon_y:.2f}" r="8" '
            f'fill="#FFFFFF" stroke="{group.stroke}" stroke-width="0.8"/>'
        )
        parts.append(
            f'<path d="M{icon_x - 4:.2f},{icon_y + 2:.2f} l3,-5 l3,4 l3,-6" '
            f'fill="none" stroke="{group.stroke}" stroke-width="0.8"/>'
        )
    else:
        parts.append(_dot_row_icon(Rect(icon_x - 10, icon_y - 6, 20, 12), group.stroke, group.stroke))
    parts.append(
        _text(
            _wrap(group.label, group.rect.width - 58, 12.2, max_lines=1),
            group.rect.x + 39,
            group.rect.y + 26,
            font_size=12.2,
            fill=style["text_primary"],
            weight=700,
            anchor="start",
            family=family,
        )
    )
    return "".join(parts)


def _group_svg(group: ResolvedGroup, family: str, style: dict, style_id: str, index: int) -> str:
    if style_id == "s1-compact-modular":
        body = _group_s1(group, family, style)
    elif style_id == "s2-multi-panel":
        body = _group_s2(group, family, style)
    elif style_id == "s3-dense-engineering":
        body = _group_s3(group, family, style, index)
    elif style_id == "s4-macro-partition":
        body = _group_s4(group, family, style)
    elif style_id == "s5-rigorous-graph":
        body = _group_s5(group, family, style)
    else:
        body = _group_s6(group, family, style, index)
    return f'<g id="group-{_esc(group.id)}">{body}</g>'


def _edge_path(edge: ResolvedEdge, marker_id: str, *, style_id: str) -> str:
    if len(edge.points) < 2:
        return ""
    path = f"M {edge.points[0][0]:.2f},{edge.points[0][1]:.2f} " + " ".join(
        f"L {x:.2f},{y:.2f}" for x, y in edge.points[1:]
    )
    dash = ' stroke-dasharray="7 5"' if edge.dashed else ""
    marker = f' marker-end="url(#{marker_id})"' if edge.arrow in {"end", "both"} else ""
    start_marker = f' marker-start="url(#{marker_id})"' if edge.arrow == "both" else ""
    line_join = "miter" if style_id == "s3-dense-engineering" else "round"
    return (
        f'<path id="edge-{_esc(edge.id)}" d="{path}" fill="none" stroke="{edge.color}" '
        f'stroke-width="{edge.width:.2f}" stroke-linejoin="{line_join}" stroke-linecap="round"'
        f'{dash}{marker}{start_marker}/>'
    )


def _annotation_svg(annotation, family: str, style: dict, style_id: str) -> str:
    if style_id == "s3-dense-engineering":
        radius = 1.5
        fill = "#FFFFFF"
    elif style_id == "s6-paperbanana-soft":
        radius = 7
        fill = "#FBFAFA"
    else:
        radius = 5
        fill = annotation.fill
    parts = [f'<g id="annotation-{_esc(annotation.id)}">']
    parts.append(
        _rounded_rect(
            annotation.rect,
            fill,
            annotation.stroke,
            0.8,
            radius,
            dashed=annotation.kind == "reference",
            opacity=0.94,
        )
    )
    lines: list[str] = []
    for raw in annotation.text.splitlines() or [""]:
        lines.extend(_wrap(raw, annotation.rect.width - 22, annotation.font_size, max_lines=3))
    parts.append(
        _text(
            lines,
            annotation.rect.x + 12,
            annotation.rect.y + 17,
            font_size=annotation.font_size,
            fill=annotation.text_color,
            weight=400,
            anchor="start",
            family=family,
            line_height=1.15,
        )
    )
    parts.append("</g>")
    return "".join(parts)


def _template_background(fig: ResolvedFigure, style: dict) -> str:
    width, height = fig.canvas.width, fig.canvas.height
    style_id = fig.style_id
    parts: list[str] = []
    if style_id == "s1-compact-modular":
        parts.append(_line(32, 84, width - 32, 84, "#D7D7D5", 0.65))
    elif style_id == "s2-multi-panel":
        parts.append(
            f'<rect x="20" y="86" width="{width - 40}" height="{height - 128}" '
            f'rx="10" fill="none" stroke="#D5DEE8" stroke-width="0.7"/>'
        )
    elif style_id == "s3-dense-engineering":
        for y in range(104, height - 50, 44):
            parts.append(_line(34, y, width - 34, y, "#E8EAEC", 0.35, dashed=True))
    elif style_id == "s4-macro-partition":
        parts.append(_waveform_icon(Rect(46, 45, 120, 24), "#6687BA", cycles=3.1))
        parts.append(_frequency_icon(Rect(width - 170, 39, 120, 30), "#53ABB2", "#53ABB2"))
    elif style_id == "s5-rigorous-graph":
        parts.append(_line(width / 2 - 90, 78, width / 2 + 90, 78, "#B98087", 1.0))
    else:
        parts.append(_line(40, 82, width - 40, 82, "#D3CFD6", 0.7, dashed=True))
    return "".join(parts)


def render_svg(fig: ResolvedFigure, output_path: str | Path, style: dict) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = fig.canvas.width, fig.canvas.height
    family = style.get("font_family", "Arial, sans-serif")
    title_family = style.get("title_font_family", family)
    palette = list(style.get("glyph_palette") or [])
    edge_colors = sorted({edge.color for edge in fig.edges})
    style_id = fig.style_id
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
    ]
    for color in edge_colors:
        marker_id = _hex_id(color)
        marker_size = 8 if style_id == "s3-dense-engineering" else 10
        ref_x = 7 if marker_size == 8 else 9
        parts.append(
            f'<marker id="{marker_id}" markerWidth="{marker_size}" markerHeight="{marker_size}" '
            f'refX="{ref_x}" refY="3" orient="auto" markerUnits="strokeWidth">'
            f'<path d="M0,0 L0,6 L{ref_x},3 z" fill="{color}"/></marker>'
        )
    parts.append(
        '<filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">'
        '<feDropShadow dx="0" dy="1" stdDeviation="1.4" flood-color="#64748B" flood-opacity="0.12"/>'
        '</filter>'
    )
    parts.append("</defs>")
    parts.append(f'<rect width="100%" height="100%" fill="{fig.canvas.background}"/>')
    parts.append(_template_background(fig, style))
    title_size = 31 if style_id in {"s3-dense-engineering", "s4-macro-partition"} else 33
    parts.append(
        _text(
            _wrap(fig.title, width - 160, title_size, max_lines=2),
            width / 2,
            45,
            font_size=title_size,
            fill=style["text_primary"],
            weight=700,
            family=title_family,
        )
    )
    if fig.subtitle:
        parts.append(
            _text(
                _wrap(fig.subtitle, width - 180, 14.5, max_lines=2),
                width / 2,
                70,
                font_size=14.5,
                fill=style["text_secondary"],
                weight=400,
                family=family,
                italic=True,
            )
        )
    for index, group in enumerate(sorted(fig.groups, key=lambda item: item.order)):
        parts.append(_group_svg(group, family, style, style_id, index))
    parts.append('<g id="edges">')
    for edge in fig.edges:
        parts.append(_edge_path(edge, _hex_id(edge.color), style_id=style_id))
        if edge.label and len(edge.points) >= 2:
            midpoint = edge.points[len(edge.points) // 2]
            label_lines = _wrap(edge.label, 130, 10.5, max_lines=1)
            label_width = max(28, max(len(line) for line in label_lines) * 6.2 + 12)
            label_rect = Rect(midpoint[0] - label_width / 2, midpoint[1] - 9, label_width, 18)
            parts.append(
                _rounded_rect(
                    label_rect,
                    "#FFFFFF",
                    _mix(edge.color, "#FFFFFF", 0.55),
                    0.65,
                    4,
                    opacity=0.92,
                )
            )
            parts.append(
                _text(
                    label_lines,
                    midpoint[0],
                    midpoint[1] + 3.4,
                    font_size=10.5,
                    fill=style["text_secondary"],
                    weight=600,
                    family=family,
                )
            )
    parts.append("</g>")
    parts.append('<g id="nodes">')
    for node in fig.nodes:
        parts.append(_node_svg(node, family, style_id, palette))
    parts.append("</g>")
    for annotation in fig.annotations:
        parts.append(_annotation_svg(annotation, family, style, style_id))
    style_label = fig.style_id.upper().split("-")[0]
    parts.append(
        _text(
            [style_label],
            width - 18,
            height - 13,
            font_size=10.5,
            fill="#7B8794",
            weight=600,
            anchor="end",
            family=family,
            italic=True,
        )
    )
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")
    return path
