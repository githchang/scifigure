from __future__ import annotations

import math
from collections import deque
from dataclasses import replace
from typing import Callable, Iterable

from .models import (
    FigureIR,
    GroupSpec,
    NodeSpec,
    Rect,
    ResolvedAnnotation,
    ResolvedFigure,
    ResolvedGroup,
    ResolvedNode,
)
from .style import role_colors

AUXILIARY_EDGE_TYPES = {"training_only", "gradient", "feedback", "reference"}
OUTPUT_TYPES = {"output", "prediction", "classifier", "probability", "decoder"}
INPUT_TYPES = {"input", "data", "document", "dataset", "text", "signal"}
REPRESENTATION_TYPES = {"encoder", "embedding", "feature", "backbone", "projection"}
TRAINING_TYPES = {"loss", "objective", "training"}


def _topological_order(ir: FigureIR, *, include_auxiliary: bool = False) -> list[str]:
    ids = [node.id for node in ir.nodes]
    indegree = {node_id: 0 for node_id in ids}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in ids}
    for edge in ir.edges:
        if not include_auxiliary and edge.type in AUXILIARY_EDGE_TYPES:
            continue
        if edge.source in indegree and edge.target in indegree:
            outgoing[edge.source].append(edge.target)
            indegree[edge.target] += 1
    queue = deque([node_id for node_id in ids if indegree[node_id] == 0])
    order: list[str] = []
    while queue:
        node_id = queue.popleft()
        order.append(node_id)
        for target in outgoing[node_id]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if len(order) != len(ids):
        seen = set(order)
        order.extend(node_id for node_id in ids if node_id not in seen)
    return order


def _groups(ir: FigureIR) -> list[GroupSpec]:
    return ir.groups or [GroupSpec(id="main", label="Method", role="process")]


def _grouped_nodes(ir: FigureIR) -> dict[str, list[NodeSpec]]:
    groups = _groups(ir)
    default_group = groups[0].id
    result: dict[str, list[NodeSpec]] = {group.id: [] for group in groups}
    lookup = {node.id: node for node in ir.nodes}
    for node_id in _topological_order(ir, include_auxiliary=True):
        node = lookup[node_id]
        group_id = node.group if node.group in result else default_group
        result.setdefault(group_id, []).append(node)
    return result


def _is_output(node: NodeSpec) -> bool:
    return (node.role or "").lower() == "output" or node.type.lower() in OUTPUT_TYPES


def _is_input(node: NodeSpec) -> bool:
    return (node.role or "").lower() in {"input", "data"} or node.type.lower() in INPUT_TYPES


def _is_training(node: NodeSpec) -> bool:
    return (node.role or "").lower() in {"training", "loss", "objective"} or node.type.lower() in TRAINING_TYPES


def _is_representation(node: NodeSpec) -> bool:
    return (node.role or "").lower() in {"representation", "encoding"} or node.type.lower() in REPRESENTATION_TYPES


def _is_alignment(node: NodeSpec) -> bool:
    label = node.label.lower()
    return node.type.lower() in {"attention", "gate"} or any(token in label for token in ("align", "gate", "fusion"))


def _stage_buckets(ir: FigureIR) -> list[tuple[str, str, list[NodeSpec]]]:
    lookup = {node.id: node for node in ir.nodes}
    nodes = [lookup[node_id] for node_id in _topological_order(ir, include_auxiliary=True)]
    buckets = [
        ("input", "Input", [node for node in nodes if _is_input(node)]),
        ("representation", "Representation", [node for node in nodes if _is_representation(node) and not _is_input(node)]),
        (
            "fusion",
            "Interaction / Fusion",
            [
                node
                for node in nodes
                if not (_is_input(node) or _is_representation(node) or _is_training(node) or _is_output(node))
            ],
        ),
        ("training", "Training", [node for node in nodes if _is_training(node)]),
        ("output", "Output", [node for node in nodes if _is_output(node)]),
    ]
    return [(key, label, items) for key, label, items in buckets if items]


def _resolved_node(
    node: NodeSpec,
    rect: Rect,
    style: dict,
    *,
    instance_role: str = "primary",
    id_suffix: str = "",
    template_variant: str | None = None,
    metadata: dict | None = None,
    details_limit: int | None = None,
    font_size: float | None = None,
) -> ResolvedNode:
    fill, stroke, text = role_colors(style, node.role, node.type)
    dense = style.get("density") in {"high", "very_high"}
    merged_metadata = dict(node.metadata)
    if template_variant:
        merged_metadata["template_variant"] = template_variant
    if metadata:
        merged_metadata.update(metadata)
    details = list(node.details if details_limit is None else node.details[:details_limit])
    return ResolvedNode(
        id=f"{node.id}{id_suffix}",
        source_id=node.id,
        label=node.label,
        type=node.type,
        role=node.role,
        group=node.group,
        rect=rect,
        fill=fill,
        stroke=stroke,
        text_color=text,
        border_width=float(style.get("node_border_width", 1.5)),
        radius=float(style.get("node_radius", 10)),
        font_size=float(font_size if font_size is not None else (13 if dense else 16)),
        font_weight=650,
        details=details,
        dimension=node.dimension,
        note=node.note,
        instance_role=instance_role,
        locked=node.locked,
        metadata=merged_metadata,
    )


def _group_color(style: dict, index: int) -> str:
    colors = style.get("group_colors") or ["#F4F7FA"]
    return colors[index % len(colors)]


def _make_group(
    group_id: str,
    label: str,
    role: str,
    rect: Rect,
    style: dict,
    index: int,
    *,
    dashed: bool | None = None,
    fill: str | None = None,
    stroke: str | None = None,
) -> ResolvedGroup:
    group_fill = fill or _group_color(style, index)
    _, semantic_stroke, _ = role_colors(style, role, role)
    return ResolvedGroup(
        id=group_id,
        label=label,
        role=role,
        rect=rect,
        fill=group_fill,
        stroke=stroke or semantic_stroke,
        dashed=style.get("group_dashed", False) if dashed is None else dashed,
        title_fill=group_fill,
        order=index,
    )


def _annotations(ir: FigureIR, y: float, style: dict) -> list[ResolvedAnnotation]:
    result: list[ResolvedAnnotation] = []
    x = ir.canvas.margin
    available = ir.canvas.width - 2 * ir.canvas.margin
    for annotation in ir.annotations[:4]:
        width = min(available, min(520, max(230, 7.8 * len(annotation.text))))
        result.append(
            ResolvedAnnotation(
                id=annotation.id,
                text=annotation.text,
                rect=Rect(x, y, width, 42),
                kind=annotation.kind,
                fill="#FFFFFF",
                stroke="#CBD5E1",
                text_color=style["text_secondary"],
                font_size=12,
            )
        )
        x += width + 12
    return result


def _grid_nodes(
    nodes: list[NodeSpec],
    area: Rect,
    style: dict,
    *,
    columns: int,
    gap_x: float = 12,
    gap_y: float = 12,
    instance_role: str = "primary",
    id_suffix: str = "",
    variant: str = "card",
    details_limit: int | None = None,
    font_size: float | None = None,
    metadata_factory: Callable[[int, NodeSpec], dict] | None = None,
) -> list[ResolvedNode]:
    if not nodes:
        return []
    columns = max(1, min(columns, len(nodes)))
    rows = math.ceil(len(nodes) / columns)
    cell_width = (area.width - gap_x * (columns - 1)) / columns
    cell_height = (area.height - gap_y * (rows - 1)) / rows
    result: list[ResolvedNode] = []
    for index, node in enumerate(nodes):
        column, row = index % columns, index // columns
        rect = Rect(
            area.x + column * (cell_width + gap_x),
            area.y + row * (cell_height + gap_y),
            cell_width,
            cell_height,
        )
        result.append(
            _resolved_node(
                node,
                rect,
                style,
                instance_role=instance_role,
                id_suffix=id_suffix,
                template_variant=variant,
                metadata=metadata_factory(index, node) if metadata_factory else None,
                details_limit=details_limit,
                font_size=font_size,
            )
        )
    return result


def _join_labels(groups: Iterable[GroupSpec], fallback: str) -> str:
    labels = [group.label for group in groups if group.label]
    return " · ".join(labels) if labels else fallback


def _layout_compact(ir: FigureIR, style: dict) -> tuple[list[ResolvedGroup], list[ResolvedNode], list[ResolvedAnnotation]]:
    width, height, margin = ir.canvas.width, ir.canvas.height, ir.canvas.margin
    main_rect = Rect(margin, 88, width - 2 * margin, 318)
    source_groups = _groups(ir)
    grouped = _grouped_nodes(ir)
    stages = _stage_buckets(ir)
    resolved_groups = [
        _make_group(
            "s1-main-flow",
            "Main Architecture",
            "process",
            main_rect,
            style,
            0,
            dashed=True,
            fill="#FFFFFF",
            stroke="#A0A09F",
        )
    ]
    resolved_nodes: list[ResolvedNode] = []
    stage_gap = 16
    stage_width = (main_rect.width - 48 - stage_gap * (len(stages) - 1)) / max(1, len(stages))
    x = main_rect.x + 24
    for stage_index, (stage_key, _, stage_nodes) in enumerate(stages, 1):
        stage_area = Rect(x, main_rect.y + 64, stage_width, main_rect.height - 88)
        resolved_nodes.extend(
            _grid_nodes(
                stage_nodes,
                stage_area,
                style,
                columns=1 if len(stage_nodes) <= 3 else 2,
                gap_x=8,
                gap_y=10,
                variant="s1-main",
                details_limit=0,
                font_size=12.5,
                metadata_factory=lambda i, n, si=stage_index, sk=stage_key: {
                    "stage_index": si,
                    "stage_key": sk,
                },
            )
        )
        x += stage_width + stage_gap

    detail_y = main_rect.bottom + 18
    detail_height = height - detail_y - 48
    panel_count = min(3, max(1, len(source_groups)))
    panel_gap = 16
    panel_width = (width - 2 * margin - panel_gap * (panel_count - 1)) / panel_count
    chunks: list[list[GroupSpec]] = [[] for _ in range(panel_count)]
    for index, group in enumerate(source_groups):
        chunks[index % panel_count].append(group)
    for panel_index, chunk in enumerate(chunks):
        panel_rect = Rect(
            margin + panel_index * (panel_width + panel_gap),
            detail_y,
            panel_width,
            detail_height,
        )
        role = chunk[0].role if chunk else "process"
        resolved_groups.append(
            _make_group(
                f"s1-detail-{panel_index + 1}",
                _join_labels(chunk, f"Detail {panel_index + 1}"),
                role,
                panel_rect,
                style,
                panel_index + 1,
                dashed=True,
                fill="#FFFFFF",
                stroke="#B0B0AF",
            )
        )
        detail_nodes = [node for group in chunk for node in grouped.get(group.id, [])]
        detail_area = Rect(panel_rect.x + 18, panel_rect.y + 50, panel_rect.width - 36, panel_rect.height - 66)
        resolved_nodes.extend(
            _grid_nodes(
                detail_nodes,
                detail_area,
                style,
                columns=2 if len(detail_nodes) > 3 and detail_area.width > 300 else 1,
                gap_x=8,
                gap_y=8,
                instance_role="detail",
                id_suffix=f"__s1detail{panel_index}",
                variant="s1-detail",
                details_limit=1,
                font_size=10.5,
            )
        )
    return resolved_groups, resolved_nodes, _annotations(ir, height - 43, style)


def _layout_multi_panel(ir: FigureIR, style: dict) -> tuple[list[ResolvedGroup], list[ResolvedNode], list[ResolvedAnnotation]]:
    width, height, margin = ir.canvas.width, ir.canvas.height, ir.canvas.margin
    title_height = 88
    footer_height = 46
    left_width = width * 0.34
    left_rect = Rect(margin, title_height, left_width, height - title_height - footer_height)
    right_x = left_rect.right + 20
    right_width = width - margin - right_x
    resolved_groups = [
        _make_group("s2-overview", "Overall Workflow", "process", left_rect, style, 0, dashed=False, stroke="#6D849E")
    ]
    lookup = {node.id: node for node in ir.nodes}
    ordered_nodes = [lookup[node_id] for node_id in _topological_order(ir, include_auxiliary=True)]
    overview_area = Rect(left_rect.x + 20, left_rect.y + 52, left_rect.width - 40, left_rect.height - 70)
    resolved_nodes = _grid_nodes(
        ordered_nodes,
        overview_area,
        style,
        columns=2 if len(ordered_nodes) > 8 else 1,
        gap_x=9,
        gap_y=7,
        variant="s2-overview",
        details_limit=0,
        font_size=11.5,
    )
    source_groups = _groups(ir)
    grouped = _grouped_nodes(ir)
    columns = 2
    rows = math.ceil(len(source_groups) / columns)
    panel_gap = 14
    panel_width = (right_width - panel_gap * (columns - 1)) / columns
    panel_height = (left_rect.height - panel_gap * (rows - 1)) / rows
    letters = "abcdefghijklmnopqrstuvwxyz"
    for index, group in enumerate(source_groups):
        column, row = index % columns, index // columns
        panel_rect = Rect(
            right_x + column * (panel_width + panel_gap),
            title_height + row * (panel_height + panel_gap),
            panel_width,
            panel_height,
        )
        panel_label = f"({letters[index]}) {group.label}" if index < len(letters) else group.label
        resolved_groups.append(
            _make_group(f"s2-panel-{group.id}", panel_label, group.role, panel_rect, style, index + 1, dashed=False)
        )
        panel_nodes = grouped.get(group.id, [])
        panel_area = Rect(panel_rect.x + 16, panel_rect.y + 48, panel_rect.width - 32, panel_rect.height - 62)
        resolved_nodes.extend(
            _grid_nodes(
                panel_nodes,
                panel_area,
                style,
                columns=2 if len(panel_nodes) > 3 else 1,
                gap_x=8,
                gap_y=8,
                instance_role="detail",
                id_suffix=f"__s2panel{index}",
                variant="s2-panel",
                details_limit=1,
                font_size=10.5,
                metadata_factory=lambda i, n, pi=index: {
                    "panel_index": pi,
                    "panel_letter": letters[pi],
                },
            )
        )
    return resolved_groups, resolved_nodes, _annotations(ir, height - 43, style)


def _layout_dense(ir: FigureIR, style: dict) -> tuple[list[ResolvedGroup], list[ResolvedNode], list[ResolvedAnnotation]]:
    width, height, margin = ir.canvas.width, ir.canvas.height, ir.canvas.margin
    title_height = 90
    footer_height = 44
    stages = _stage_buckets(ir)
    stage_gap = 10
    stage_width = (width - 2 * margin - stage_gap * (len(stages) - 1)) / max(1, len(stages))
    area_height = height - title_height - footer_height
    resolved_groups: list[ResolvedGroup] = []
    resolved_nodes: list[ResolvedNode] = []
    for stage_index, (stage_key, stage_label, stage_nodes) in enumerate(stages, 1):
        x = margin + (stage_index - 1) * (stage_width + stage_gap)
        stage_rect = Rect(x, title_height, stage_width, area_height)
        role = str(stage_nodes[0].role or stage_key) if stage_nodes else stage_key
        resolved_groups.append(
            _make_group(
                f"s3-stage-{stage_index}",
                stage_label,
                role,
                stage_rect,
                style,
                stage_index - 1,
                dashed=True,
                fill="#FFFFFF",
                stroke="#5B7F55" if stage_index in {1, len(stages)} else None,
            )
        )
        inner = Rect(stage_rect.x + 14, stage_rect.y + 62, stage_rect.width - 28, stage_rect.height - 80)
        resolved_nodes.extend(
            _grid_nodes(
                stage_nodes,
                inner,
                style,
                columns=1 if len(stage_nodes) <= 4 else 2,
                gap_x=7,
                gap_y=9,
                variant="s3-stage",
                details_limit=1,
                font_size=10.8,
                metadata_factory=lambda i, n, si=stage_index, sk=stage_key: {
                    "stage_index": si,
                    "stage_key": sk,
                    "engineering_index": i + 1,
                },
            )
        )
    return resolved_groups, resolved_nodes, _annotations(ir, height - 41, style)


def _layout_macro(ir: FigureIR, style: dict) -> tuple[list[ResolvedGroup], list[ResolvedNode], list[ResolvedAnnotation]]:
    width, height, margin = ir.canvas.width, ir.canvas.height, ir.canvas.margin
    title_height = 92
    footer_height = 44
    left_width = width * 0.47
    left_rect = Rect(margin, title_height, left_width, height - title_height - footer_height)
    right_x = left_rect.right + 20
    right_width = width - margin - right_x
    top_panel = Rect(right_x, title_height, right_width, (left_rect.height - 20) * 0.48)
    bottom_panel = Rect(right_x, top_panel.bottom + 20, right_width, left_rect.bottom - top_panel.bottom - 20)
    resolved_groups = [
        _make_group("s4-main-model", "Main Model Flow", "process", left_rect, style, 0, dashed=False, fill="#FFFFFF", stroke="#49A2AA"),
        _make_group("s4-upper-panel", "Interaction / Projection Details", "fusion", top_panel, style, 1, dashed=False, fill="#FFFFFF", stroke="#49A2AA"),
        _make_group("s4-lower-panel", "Input / Representation Details", "representation", bottom_panel, style, 2, dashed=False, fill="#FFFFFF", stroke="#7994B9"),
    ]
    stage_map = {key: nodes for key, _, nodes in _stage_buckets(ir)}
    stage_sequence = ["output", "training", "fusion", "representation", "input"]
    stage_nodes = [(key, stage_map.get(key, [])) for key in stage_sequence if stage_map.get(key)]
    training_nodes = stage_map.get("training", [])
    resolved_nodes: list[ResolvedNode] = []
    main_inner = Rect(left_rect.x + 22, left_rect.y + 54, left_rect.width - 44, left_rect.height - 76)
    lane_gap = 14
    lane_height = (main_inner.height - lane_gap * (len(stage_nodes) - 1)) / max(1, len(stage_nodes))
    for lane_index, (stage_key, nodes) in enumerate(stage_nodes):
        lane_area = Rect(
            main_inner.x,
            main_inner.y + lane_index * (lane_height + lane_gap),
            main_inner.width,
            lane_height,
        )
        resolved_nodes.extend(
            _grid_nodes(
                nodes,
                lane_area,
                style,
                columns=min(3, max(1, len(nodes))),
                gap_x=10,
                gap_y=8,
                variant="s4-main",
                details_limit=0,
                font_size=11.5,
                metadata_factory=lambda i, n, sk=stage_key, li=lane_index: {
                    "lane_key": sk,
                    "lane_index": li,
                },
            )
        )
    fusion_details = stage_map.get("fusion", []) + training_nodes
    resolved_nodes.extend(
        _grid_nodes(
            fusion_details,
            Rect(top_panel.x + 18, top_panel.y + 52, top_panel.width - 36, top_panel.height - 68),
            style,
            columns=2 if len(fusion_details) > 2 else 1,
            gap_x=10,
            gap_y=10,
            instance_role="detail",
            id_suffix="__s4upper",
            variant="s4-analysis",
            details_limit=1,
            font_size=10.5,
        )
    )
    representation_details = stage_map.get("input", []) + stage_map.get("representation", [])
    resolved_nodes.extend(
        _grid_nodes(
            representation_details,
            Rect(bottom_panel.x + 18, bottom_panel.y + 52, bottom_panel.width - 36, bottom_panel.height - 68),
            style,
            columns=2 if len(representation_details) > 2 else 1,
            gap_x=10,
            gap_y=10,
            instance_role="detail",
            id_suffix="__s4lower",
            variant="s4-analysis",
            details_limit=1,
            font_size=10.5,
        )
    )
    return resolved_groups, resolved_nodes, _annotations(ir, height - 41, style)


def _layout_rigorous(ir: FigureIR, style: dict) -> tuple[list[ResolvedGroup], list[ResolvedNode], list[ResolvedAnnotation]]:
    width, height, margin = ir.canvas.width, ir.canvas.height, ir.canvas.margin
    title_height = 92
    footer_height = 44
    left_width = 245
    right_width = 275
    center_x = margin + left_width + 24
    center_width = width - 2 * margin - left_width - right_width - 48
    content_height = height - title_height - footer_height
    input_rect = Rect(margin, title_height, left_width, content_height)
    upper_rect = Rect(center_x, title_height, center_width, 270)
    alignment_rect = Rect(center_x, upper_rect.bottom + 20, center_width, 112)
    branches_rect = Rect(center_x, alignment_rect.bottom + 20, center_width, content_height - 422)
    output_rect = Rect(center_x + center_width + 24, title_height, right_width, content_height)
    resolved_groups = [
        _make_group("s5-input", "Input / Foundation", "input", input_rect, style, 0, dashed=True, fill="#FFFFFF"),
        _make_group("s5-upper", "Structured Gating", "fusion", upper_rect, style, 1, dashed=False, fill="#FEFDF8"),
        _make_group("s5-alignment", "Alignment Layer", "representation", alignment_rect, style, 2, dashed=False, fill="#FBFCFD", stroke="#6689B2"),
        _make_group("s5-branches", "Specialized Branches", "process", branches_rect, style, 3, dashed=False, fill="#FEFDF8"),
        _make_group("s5-output", "Output", "output", output_rect, style, 4, dashed=False, fill="#FFFFFF"),
    ]
    lookup = {node.id: node for node in ir.nodes}
    ordered = [lookup[node_id] for node_id in _topological_order(ir, include_auxiliary=True)]
    input_nodes = [node for node in ordered if _is_input(node)]
    output_nodes = [node for node in ordered if _is_output(node)]
    training_nodes = [node for node in ordered if _is_training(node)]
    middle_nodes = [
        node
        for node in ordered
        if node not in input_nodes and node not in output_nodes and node not in training_nodes
    ]
    alignment_node = next(
        (node for node in middle_nodes if _is_alignment(node)),
        middle_nodes[len(middle_nodes) // 2] if middle_nodes else None,
    )
    upper_nodes = [node for node in middle_nodes if node is not alignment_node]
    branch_nodes = list(training_nodes)
    if len(upper_nodes) > 4:
        branch_nodes = upper_nodes[4:] + branch_nodes
        upper_nodes = upper_nodes[:4]
    resolved_nodes: list[ResolvedNode] = []
    resolved_nodes.extend(
        _grid_nodes(
            input_nodes,
            Rect(input_rect.x + 18, input_rect.y + 52, input_rect.width - 36, input_rect.height - 70),
            style,
            columns=1,
            gap_y=16,
            variant="s5-input",
            details_limit=1,
            font_size=11.5,
        )
    )
    resolved_nodes.extend(
        _grid_nodes(
            upper_nodes,
            Rect(upper_rect.x + 22, upper_rect.y + 54, upper_rect.width - 44, upper_rect.height - 72),
            style,
            columns=2 if len(upper_nodes) > 2 else max(1, len(upper_nodes)),
            gap_x=22,
            gap_y=14,
            variant="s5-gate-card",
            details_limit=1,
            font_size=11.5,
            metadata_factory=lambda i, n: {"gate_index": i + 1},
        )
    )
    if alignment_node:
        resolved_nodes.append(
            _resolved_node(
                alignment_node,
                Rect(alignment_rect.x + 50, alignment_rect.y + 42, alignment_rect.width - 100, 56),
                style,
                template_variant="s5-alignment-band",
                metadata={"alignment_band": True},
                details_limit=0,
                font_size=13,
            )
        )
    resolved_nodes.extend(
        _grid_nodes(
            branch_nodes,
            Rect(branches_rect.x + 22, branches_rect.y + 54, branches_rect.width - 44, branches_rect.height - 72),
            style,
            columns=min(3, max(1, len(branch_nodes))),
            gap_x=18,
            gap_y=12,
            variant="s5-branch",
            details_limit=1,
            font_size=10.8,
            metadata_factory=lambda i, n: {"branch_index": i + 1},
        )
    )
    resolved_nodes.extend(
        _grid_nodes(
            output_nodes,
            Rect(output_rect.x + 18, output_rect.y + 52, output_rect.width - 36, output_rect.height - 70),
            style,
            columns=1,
            gap_y=18,
            variant="s5-output",
            details_limit=1,
            font_size=11.5,
        )
    )
    return resolved_groups, resolved_nodes, _annotations(ir, height - 41, style)


def _layout_paperbanana(ir: FigureIR, style: dict) -> tuple[list[ResolvedGroup], list[ResolvedNode], list[ResolvedAnnotation]]:
    width, height, margin = ir.canvas.width, ir.canvas.height, ir.canvas.margin
    title_height = 94
    footer_height = 44
    output_width = 250
    gap = 22
    main_width = width - 2 * margin - output_width - gap
    band_gap = 22
    band_height = (height - title_height - footer_height - band_gap) / 2
    upper_rect = Rect(margin, title_height, main_width, band_height)
    lower_rect = Rect(margin, upper_rect.bottom + band_gap, main_width, band_height)
    output_rect = Rect(upper_rect.right + gap, title_height, output_width, height - title_height - footer_height)
    lookup = {node.id: node for node in ir.nodes}
    ordered = [lookup[node_id] for node_id in _topological_order(ir, include_auxiliary=True)]
    output_nodes = [node for node in ordered if _is_output(node)]
    remaining = [node for node in ordered if node not in output_nodes]
    upper_nodes = [node for node in remaining if _is_input(node) or _is_representation(node)]
    lower_nodes = [node for node in remaining if node not in upper_nodes]
    if not lower_nodes and len(upper_nodes) > 1:
        split = max(1, len(upper_nodes) // 2)
        lower_nodes = upper_nodes[split:]
        upper_nodes = upper_nodes[:split]
    if not upper_nodes and lower_nodes:
        split = max(1, len(lower_nodes) // 2)
        upper_nodes = lower_nodes[:split]
        lower_nodes = lower_nodes[split:]
    source_groups = _groups(ir)
    upper_group_ids = {node.group for node in upper_nodes}
    lower_group_ids = {node.group for node in lower_nodes}
    upper_label = _join_labels(
        [group for group in source_groups if group.id in upper_group_ids],
        "Primary Reasoning",
    )
    lower_label = _join_labels(
        [group for group in source_groups if group.id in lower_group_ids],
        "Latent Processing",
    )
    resolved_groups = [
        _make_group("s6-upper", upper_label, "representation", upper_rect, style, 0, dashed=False, fill="#FCFCFB", stroke="#A5A5A0"),
        _make_group("s6-lower", lower_label, "process", lower_rect, style, 1, dashed=False, fill="#FBFAFA", stroke="#AAA0AF"),
        _make_group("s6-output", "Outputs", "output", output_rect, style, 2, dashed=False, fill="#FCFCFC", stroke="#A5A5A0"),
    ]
    resolved_nodes: list[ResolvedNode] = []
    resolved_nodes.extend(
        _grid_nodes(
            upper_nodes,
            Rect(upper_rect.x + 26, upper_rect.y + 58, upper_rect.width - 52, upper_rect.height - 82),
            style,
            columns=min(4, max(1, len(upper_nodes))),
            gap_x=18,
            gap_y=14,
            variant="s6-narrative-upper",
            details_limit=1,
            font_size=11.5,
            metadata_factory=lambda i, n: {"narrative_band": "upper", "sequence_index": i + 1},
        )
    )
    resolved_nodes.extend(
        _grid_nodes(
            lower_nodes,
            Rect(lower_rect.x + 26, lower_rect.y + 58, lower_rect.width - 52, lower_rect.height - 82),
            style,
            columns=min(4, max(1, len(lower_nodes))),
            gap_x=18,
            gap_y=14,
            variant="s6-narrative-lower",
            details_limit=1,
            font_size=11.5,
            metadata_factory=lambda i, n: {"narrative_band": "lower", "sequence_index": i + 1},
        )
    )
    resolved_nodes.extend(
        _grid_nodes(
            output_nodes,
            Rect(output_rect.x + 20, output_rect.y + 60, output_rect.width - 40, output_rect.height - 84),
            style,
            columns=1,
            gap_y=20,
            variant="s6-output",
            details_limit=1,
            font_size=11.5,
        )
    )
    return resolved_groups, resolved_nodes, _annotations(ir, height - 41, style)


def resolve_layout(ir: FigureIR, style: dict) -> ResolvedFigure:
    layout = style.get("layout", "paperbanana_soft")
    if layout == "compact_modular":
        groups, nodes, annotations = _layout_compact(ir, style)
    elif layout == "multi_panel":
        groups, nodes, annotations = _layout_multi_panel(ir, style)
    elif layout == "dense_engineering":
        groups, nodes, annotations = _layout_dense(ir, style)
    elif layout == "macro_partition":
        groups, nodes, annotations = _layout_macro(ir, style)
    elif layout == "rigorous_graph":
        groups, nodes, annotations = _layout_rigorous(ir, style)
    else:
        groups, nodes, annotations = _layout_paperbanana(ir, style)
    canvas = replace(ir.canvas, background=style.get("canvas_background", ir.canvas.background))
    return ResolvedFigure(
        title=ir.title,
        subtitle=ir.subtitle,
        style_id=style["id"],
        canvas=canvas,
        groups=groups,
        nodes=nodes,
        edges=[],
        annotations=annotations,
        legend=[("solid", "Data / process flow"), ("dashed", "Auxiliary / training / reference")],
        metadata={
            "style_name": style.get("display_name", style["id"]),
            "figure_type": ir.figure_type,
            "template_locked": bool(style.get("template_locked", False)),
            "reference_template": style.get("reference_template"),
            "template_rules": dict(style.get("template_rules") or {}),
        },
    )
