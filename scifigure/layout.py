from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import replace
from typing import Iterable

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


def _topological_order(ir: FigureIR) -> list[str]:
    ids = [n.id for n in ir.nodes]
    indegree = {nid: 0 for nid in ids}
    outgoing: dict[str, list[str]] = {nid: [] for nid in ids}
    for e in ir.edges:
        if e.source in indegree and e.target in indegree:
            outgoing[e.source].append(e.target)
            indegree[e.target] += 1
    q = deque([nid for nid in ids if indegree[nid] == 0])
    order: list[str] = []
    while q:
        nid = q.popleft()
        order.append(nid)
        for nxt in outgoing[nid]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                q.append(nxt)
    if len(order) != len(ids):
        seen = set(order)
        order.extend(nid for nid in ids if nid not in seen)
    return order


def _depths(ir: FigureIR) -> dict[str, int]:
    order = _topological_order(ir)
    pred: dict[str, list[str]] = defaultdict(list)
    for e in ir.edges:
        pred[e.target].append(e.source)
    depth: dict[str, int] = {}
    for nid in order:
        depth[nid] = max((depth.get(p, 0) + 1 for p in pred[nid]), default=0)
    return depth


def _groups(ir: FigureIR) -> list[GroupSpec]:
    if ir.groups:
        return ir.groups
    return [GroupSpec(id="main", label="Method", role="process")]


def _grouped_nodes(ir: FigureIR) -> dict[str, list[NodeSpec]]:
    groups = _groups(ir)
    default = groups[0].id
    result: dict[str, list[NodeSpec]] = {g.id: [] for g in groups}
    order = _topological_order(ir)
    lookup = {n.id: n for n in ir.nodes}
    for nid in order:
        n = lookup[nid]
        gid = n.group if n.group in result else default
        result.setdefault(gid, []).append(n)
    return result


def _node_height(node: NodeSpec, base: float, dense: bool = False) -> float:
    details = min(len(node.details), 3)
    extra = 12 * details + (12 if node.dimension else 0) + (10 if node.note else 0)
    if dense:
        extra *= 0.55
    return base + extra


def _resolved_node(node: NodeSpec, rect: Rect, style: dict, *, instance_role: str = "primary", id_suffix: str = "") -> ResolvedNode:
    fill, stroke, text = role_colors(style, node.role, node.type)
    dense = style.get("density") in {"high", "very_high"}
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
        font_size=14 if dense else 16,
        font_weight=650,
        details=node.details,
        dimension=node.dimension,
        note=node.note,
        instance_role=instance_role,
        locked=node.locked,
        metadata=dict(node.metadata),
    )


def _group_color(style: dict, idx: int) -> str:
    colors = style.get("group_colors") or ["#F4F7FA"]
    return colors[idx % len(colors)]


def _make_group(g: GroupSpec, rect: Rect, style: dict, idx: int, *, dashed: bool | None = None) -> ResolvedGroup:
    fill = _group_color(style, idx)
    _, stroke, _ = role_colors(style, g.role, g.role)
    return ResolvedGroup(
        id=g.id,
        label=g.label,
        role=g.role,
        rect=rect,
        fill=fill,
        stroke=stroke,
        dashed=style.get("group_dashed", False) if dashed is None else dashed,
        title_fill=fill,
        order=idx,
    )


def _annotations(ir: FigureIR, y: float, style: dict) -> list[ResolvedAnnotation]:
    result: list[ResolvedAnnotation] = []
    x = ir.canvas.margin
    for i, a in enumerate(ir.annotations[:4]):
        w = min(340, max(180, 8.5 * len(a.text)))
        result.append(ResolvedAnnotation(
            id=a.id, text=a.text, rect=Rect(x, y, w, 48), kind=a.kind,
            fill="#FFFFFF", stroke="#CBD5E1", text_color=style["text_secondary"], font_size=13,
        ))
        x += w + 12
    return result


def _layout_paperbanana(ir: FigureIR, style: dict) -> tuple[list[ResolvedGroup], list[ResolvedNode], list[ResolvedAnnotation]]:
    groups = _groups(ir)
    grouped = _grouped_nodes(ir)
    W, H, m = ir.canvas.width, ir.canvas.height, ir.canvas.margin
    title_h = 88
    bottom_h = 82 if ir.annotations else 28
    area_y = title_h
    area_h = H - title_h - bottom_h
    gap = 18
    total_nodes = max(1, sum(len(v) for v in grouped.values()))
    min_group_w = 210
    available = W - 2 * m - gap * (len(groups) - 1)
    weights = [max(1.0, len(grouped.get(g.id, [])) * 0.85) for g in groups]
    wsum = sum(weights)
    widths = [max(min_group_w, available * w / wsum) for w in weights]
    if sum(widths) > available:
        scale = available / sum(widths)
        widths = [w * scale for w in widths]
    resolved_groups: list[ResolvedGroup] = []
    nodes: list[ResolvedNode] = []
    x = m
    for gi, (g, gw) in enumerate(zip(groups, widths)):
        grect = Rect(x, area_y, gw, area_h)
        resolved_groups.append(_make_group(g, grect, style, gi))
        group_nodes = grouped.get(g.id, [])
        inner_x = x + 18
        inner_y = area_y + 52
        inner_w = gw - 36
        if len(group_nodes) <= 3:
            nh = min(132, (area_h - 72 - gap * max(0, len(group_nodes)-1)) / max(1, len(group_nodes)))
            for ni, n in enumerate(group_nodes):
                h = max(72, _node_height(n, nh, dense=False))
                rect = Rect(inner_x, inner_y, inner_w, min(h, 138))
                nodes.append(_resolved_node(n, rect, style))
                inner_y += rect.height + gap
        else:
            cols = 2 if inner_w > 280 else 1
            cell_gap = 12
            nw = (inner_w - cell_gap * (cols - 1)) / cols
            rows = math.ceil(len(group_nodes) / cols)
            nh = max(78, min(118, (area_h - 68 - cell_gap * (rows - 1)) / rows))
            for ni, n in enumerate(group_nodes):
                col, row = ni % cols, ni // cols
                rect = Rect(inner_x + col * (nw + cell_gap), inner_y + row * (nh + cell_gap), nw, nh)
                nodes.append(_resolved_node(n, rect, style))
        x += gw + gap
    annotations = _annotations(ir, H - bottom_h + 10, style)
    return resolved_groups, nodes, annotations


def _layout_macro(ir: FigureIR, style: dict) -> tuple[list[ResolvedGroup], list[ResolvedNode], list[ResolvedAnnotation]]:
    groups = _groups(ir)
    grouped = _grouped_nodes(ir)
    W, H, m = ir.canvas.width, ir.canvas.height, ir.canvas.margin
    title_h = 96
    area_h = H - title_h - 52
    gap = 24
    cols = min(3, max(1, len(groups)))
    rows = math.ceil(len(groups) / cols)
    gw = (W - 2*m - gap*(cols-1)) / cols
    gh = (area_h - gap*(rows-1)) / rows
    rgroups: list[ResolvedGroup] = []
    rnodes: list[ResolvedNode] = []
    for gi, g in enumerate(groups):
        c, r = gi % cols, gi // cols
        gx = m + c*(gw+gap)
        gy = title_h + r*(gh+gap)
        grect = Rect(gx, gy, gw, gh)
        rgroups.append(_make_group(g, grect, style, gi))
        ns = grouped.get(g.id, [])
        inner = Rect(gx+24, gy+58, gw-48, gh-82)
        if not ns:
            continue
        if len(ns) <= 2:
            nw = inner.width
            nh = min(130, (inner.height - 16*(len(ns)-1))/len(ns))
            for i,n in enumerate(ns):
                rct=Rect(inner.x, inner.y+i*(nh+16), nw, nh)
                rnodes.append(_resolved_node(n,rct,style))
        else:
            cols_n = 2 if inner.width >= 360 else 1
            rows_n = math.ceil(len(ns)/cols_n)
            cg=14
            nw=(inner.width-cg*(cols_n-1))/cols_n
            nh=max(74,min(112,(inner.height-cg*(rows_n-1))/rows_n))
            for i,n in enumerate(ns):
                c2,r2=i%cols_n,i//cols_n
                rct=Rect(inner.x+c2*(nw+cg), inner.y+r2*(nh+cg),nw,nh)
                rnodes.append(_resolved_node(n,rct,style))
    return rgroups,rnodes,_annotations(ir,H-42,style)


def _layout_dense(ir: FigureIR, style: dict) -> tuple[list[ResolvedGroup], list[ResolvedNode], list[ResolvedAnnotation]]:
    W,H,m=ir.canvas.width,ir.canvas.height,ir.canvas.margin
    title_h=88
    depths=_depths(ir)
    maxd=max(depths.values(),default=0)
    cols=maxd+1
    col_gap=18
    usable_w=W-2*m
    col_w=(usable_w-col_gap*(cols-1))/max(1,cols)
    by_depth: dict[int,list[NodeSpec]]=defaultdict(list)
    lookup={n.id:n for n in ir.nodes}
    for nid in _topological_order(ir): by_depth[depths[nid]].append(lookup[nid])
    rgroups=[]
    groups=_groups(ir)
    grouped_ids={g.id:{n.id for n in _grouped_nodes(ir).get(g.id,[])} for g in groups}
    for gi,g in enumerate(groups):
        ds=[depths[nid] for nid in grouped_ids[g.id] if nid in depths]
        if not ds: continue
        min_d,max_d=min(ds),max(ds)
        gx=m+min_d*(col_w+col_gap)-8
        gw=(max_d-min_d+1)*col_w+(max_d-min_d)*col_gap+16
        rgroups.append(_make_group(g,Rect(gx,title_h,gw,H-title_h-44),style,gi,dashed=True))
    rnodes=[]
    for d in range(cols):
        ns=by_depth.get(d,[])
        x=m+d*(col_w+col_gap)
        if not ns: continue
        gap=10
        avail=H-title_h-62
        nh=max(62,min(92,(avail-gap*(len(ns)-1))/len(ns)))
        y=title_h+34
        for i,n in enumerate(ns):
            h=max(62,min(104,_node_height(n,nh,dense=True)))
            rnodes.append(_resolved_node(n,Rect(x,y,col_w,h),style))
            y+=h+gap
    return rgroups,rnodes,_annotations(ir,H-38,style)


def _layout_rigorous(ir: FigureIR, style: dict) -> tuple[list[ResolvedGroup], list[ResolvedNode], list[ResolvedAnnotation]]:
    # Three horizontal scholarly bands with strong boundaries and a right-side output zone.
    groups=_groups(ir)
    grouped=_grouped_nodes(ir)
    W,H,m=ir.canvas.width,ir.canvas.height,ir.canvas.margin
    title_h=92
    gap=14
    right_w=290
    left_w=W-2*m-right_w-gap
    band_h=(H-title_h-44-gap*(max(1,len(groups))-1))/max(1,len(groups))
    rgroups=[]; rnodes=[]
    for gi,g in enumerate(groups):
        gy=title_h+gi*(band_h+gap)
        grect=Rect(m,gy,left_w,band_h)
        rgroups.append(_make_group(g,grect,style,gi,dashed=True))
        ns=grouped.get(g.id,[])
        if not ns: continue
        inner_x=m+120
        inner_y=gy+42
        inner_w=left_w-148
        ng=12
        nw=max(128,min(210,(inner_w-ng*(len(ns)-1))/max(1,len(ns))))
        total=nw*len(ns)+ng*(len(ns)-1)
        x=inner_x+max(0,(inner_w-total)/2)
        nh=max(66,min(104,band_h-58))
        for n in ns:
            rnodes.append(_resolved_node(n,Rect(x,inner_y,nw,nh),style))
            x+=nw+ng
    # Move semantic outputs to a dedicated right zone when possible.
    outputs=[n for n in rnodes if (n.role or '').lower()=='output' or n.type.lower() in {'output','prediction','classifier'}]
    if outputs:
        out_group=ResolvedGroup('output-zone','Outputs','output',Rect(W-m-right_w,title_h,right_w,H-title_h-44),'#F7F7F7','#777777',True,'#F7F7F7',99)
        rgroups.append(out_group)
        oy=title_h+56
        for i,n in enumerate(outputs):
            n.rect=Rect(W-m-right_w+28,oy,right_w-56,min(116,n.rect.height+12))
            n.group='output-zone'
            oy+=n.rect.height+22
    return rgroups,rnodes,_annotations(ir,H-38,style)


def _layout_compact(ir: FigureIR, style: dict) -> tuple[list[ResolvedGroup], list[ResolvedNode], list[ResolvedAnnotation]]:
    W,H,m=ir.canvas.width,ir.canvas.height,ir.canvas.margin
    title_h=86
    top_h=330
    bottom_y=title_h+top_h+20
    bottom_h=H-bottom_y-44
    order=_topological_order(ir)
    lookup={n.id:n for n in ir.nodes}
    gap=13
    nw=max(118,min(190,(W-2*m-gap*(len(order)-1))/max(1,len(order))))
    total=nw*len(order)+gap*(len(order)-1)
    x=m+max(0,(W-2*m-total)/2)
    rnodes=[]
    for i,nid in enumerate(order):
        n=lookup[nid]
        stagger=0 if i%2==0 else 18
        rnodes.append(_resolved_node(n,Rect(x,title_h+82+stagger,nw,92),style))
        x+=nw+gap
    groups=_groups(ir); grouped=_grouped_nodes(ir)
    rgroups=[ResolvedGroup('main-flow','Main Architecture','process',Rect(m,title_h,W-2*m,top_h),_group_color(style,0),'#AEB8C5',True,_group_color(style,0),0)]
    # Bottom detail panels summarize groups with detail lines; visual node instances remain primary above.
    cols=min(3,max(1,len(groups)))
    rows=math.ceil(len(groups)/cols)
    pgap=16
    pw=(W-2*m-pgap*(cols-1))/cols
    ph=(bottom_h-pgap*(rows-1))/rows
    annotations=[]
    for gi,g in enumerate(groups):
        c,r=gi%cols,gi//cols
        gx=m+c*(pw+pgap); gy=bottom_y+r*(ph+pgap)
        rgroups.append(_make_group(g,Rect(gx,gy,pw,ph),style,gi+1,dashed=True))
        ns=grouped.get(g.id,[])
        text=[]
        for n in ns:
            items=', '.join(n.details[:2])
            text.append(f"{n.label}"+(f": {items}" if items else ""))
        annotations.append(ResolvedAnnotation(
            id=f"detail-{g.id}", text='\n'.join(text) if text else g.note or 'Detail panel',
            rect=Rect(gx+18,gy+48,pw-36,ph-64),kind='detail',fill='#FFFFFF',stroke='#D5DBE4',
            text_color=style['text_secondary'],font_size=13,
        ))
    return rgroups,rnodes,annotations


def _layout_multi_panel(ir: FigureIR, style: dict) -> tuple[list[ResolvedGroup], list[ResolvedNode], list[ResolvedAnnotation]]:
    W,H,m=ir.canvas.width,ir.canvas.height,ir.canvas.margin
    title_h=88
    left_w=W*0.39
    gap=22
    right_x=m+left_w+gap
    right_w=W-m-right_x
    rgroups=[ResolvedGroup('overview','Overall Workflow','process',Rect(m,title_h,left_w,H-title_h-42),_group_color(style,0),'#9BA8B8',False,_group_color(style,0),0)]
    order=_topological_order(ir); lookup={n.id:n for n in ir.nodes}
    rnodes=[]
    y=title_h+52
    gap_y=7
    nh=max(48,min(62,(H-title_h-72-gap_y*(len(order)-1))/max(1,len(order))))
    for nid in order:
        n=lookup[nid]
        rn=_resolved_node(n,Rect(m+24,y,left_w-48,nh),style)
        # The left overview keeps the complete module sequence but suppresses
        # secondary detail text; the right panels carry the decomposed view.
        rn.font_size=12.5
        rn.details=[]
        rn.dimension=None
        rnodes.append(rn)
        y+=nh+gap_y
    groups=_groups(ir); grouped=_grouped_nodes(ir)
    cols=2 if len(groups)>1 else 1
    rows=math.ceil(len(groups)/cols)
    pgap=16
    pw=(right_w-pgap*(cols-1))/cols
    ph=(H-title_h-42-pgap*(rows-1))/rows
    annotations=[]
    letters='abcdefghijklmnopqrstuvwxyz'
    for gi,g in enumerate(groups):
        c,r=gi%cols,gi//cols
        gx=right_x+c*(pw+pgap); gy=title_h+r*(ph+pgap)
        label=f"({letters[gi]}) {g.label}" if gi<len(letters) else g.label
        rgroups.append(ResolvedGroup(f"panel-{g.id}",label,g.role,Rect(gx,gy,pw,ph),_group_color(style,gi+1),role_colors(style,g.role,g.role)[1],False,_group_color(style,gi+1),gi+1))
        ns=grouped.get(g.id,[])
        # miniature detail instances inside each panel
        if ns:
            cols_n=1 if len(ns)<=3 else 2
            cg=9
            inner=Rect(gx+18,gy+48,pw-36,ph-66)
            rows_n=math.ceil(len(ns)/cols_n)
            nw=(inner.width-cg*(cols_n-1))/cols_n
            nh2=max(48,min(76,(inner.height-cg*(rows_n-1))/rows_n))
            for ni,n in enumerate(ns):
                c2,r2=ni%cols_n,ni//cols_n
                rn=_resolved_node(n,Rect(inner.x+c2*(nw+cg),inner.y+r2*(nh2+cg),nw,nh2),style,instance_role='detail',id_suffix=f"__panel{gi}")
                rn.font_size=11.5
                rn.details=n.details[:1]
                rnodes.append(rn)
    return rgroups,rnodes,annotations


def resolve_layout(ir: FigureIR, style: dict) -> ResolvedFigure:
    layout=style.get('layout','paperbanana_soft')
    if layout=='compact_modular': groups,nodes,annotations=_layout_compact(ir,style)
    elif layout=='multi_panel': groups,nodes,annotations=_layout_multi_panel(ir,style)
    elif layout=='dense_engineering': groups,nodes,annotations=_layout_dense(ir,style)
    elif layout=='macro_partition': groups,nodes,annotations=_layout_macro(ir,style)
    elif layout=='rigorous_graph': groups,nodes,annotations=_layout_rigorous(ir,style)
    else: groups,nodes,annotations=_layout_paperbanana(ir,style)
    # Set canvas background from style while preserving dimensions.
    canvas=replace(ir.canvas,background=style.get('canvas_background',ir.canvas.background))
    return ResolvedFigure(
        title=ir.title,subtitle=ir.subtitle,style_id=style['id'],canvas=canvas,
        groups=groups,nodes=nodes,edges=[],annotations=annotations,
        legend=[('solid','Data / process flow'),('dashed','Auxiliary / training / reference')],
        metadata={'style_name':style.get('display_name',style['id']),'figure_type':ir.figure_type},
    )
