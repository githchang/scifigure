from __future__ import annotations

import html
import math
import textwrap
from pathlib import Path
from typing import Iterable

from .models import Rect, ResolvedEdge, ResolvedFigure, ResolvedNode


def _esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def _hex_id(color: str) -> str:
    return "m" + "".join(c for c in color if c.isalnum())


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


def _text(lines: list[str], x: float, y: float, *, font_size: float, fill: str, weight: int = 400,
          anchor: str = "middle", family: str = "Arial, sans-serif", line_height: float = 1.22,
          italic: bool = False) -> str:
    if not lines:
        return ""
    tspans=[]
    for i,line in enumerate(lines):
        dy="0" if i==0 else f"{font_size*line_height:.2f}"
        tspans.append(f'<tspan x="{x:.2f}" dy="{dy}">{_esc(line)}</tspan>')
    style="italic" if italic else "normal"
    return (f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" '
            f'font-family="{_esc(family)}" font-size="{font_size:.2f}" font-weight="{weight}" '
            f'font-style="{style}" fill="{fill}">' + "".join(tspans) + "</text>")


def _rounded_rect(r: Rect, fill: str, stroke: str, width: float, radius: float, dashed: bool=False, opacity: float=1.0) -> str:
    dash=' stroke-dasharray="8 6"' if dashed else ''
    return (f'<rect x="{r.x:.2f}" y="{r.y:.2f}" width="{r.width:.2f}" height="{r.height:.2f}" '
            f'rx="{radius:.2f}" fill="{fill}" fill-opacity="{opacity:.3f}" stroke="{stroke}" '
            f'stroke-width="{width:.2f}"{dash}/>' )


def _matrix_icon(r: Rect, stroke: str, fill: str) -> str:
    size=min(42,r.height*0.42,r.width*0.24); x=r.x+12; y=r.y+(r.height-size)/2
    cell=size/3; parts=[]
    for rr in range(3):
        for cc in range(3):
            op=0.35+0.12*((rr+cc)%3)
            parts.append(f'<rect x="{x+cc*cell:.2f}" y="{y+rr*cell:.2f}" width="{cell-1:.2f}" height="{cell-1:.2f}" fill="{fill}" fill-opacity="{op:.2f}" stroke="{stroke}" stroke-width="0.6"/>')
    return ''.join(parts)


def _tensor_icon(r: Rect, stroke: str, fill: str) -> str:
    x=r.x+15; y=r.y+r.height/2-22; parts=[]
    for i in range(4):
        parts.append(f'<rect x="{x+i*6:.2f}" y="{y-i*4:.2f}" width="32" height="44" rx="3" fill="{fill}" fill-opacity="{0.35+0.12*i:.2f}" stroke="{stroke}" stroke-width="1"/>')
    return ''.join(parts)


def _vector_icon(r: Rect, stroke: str, fill: str) -> str:
    x=r.x+14; y=r.cy-18; parts=[]
    for i in range(5):
        parts.append(f'<rect x="{x+i*8:.2f}" y="{y:.2f}" width="6" height="36" rx="2" fill="{fill}" fill-opacity="{0.35+0.1*i:.2f}" stroke="{stroke}" stroke-width="0.7"/>')
    return ''.join(parts)


def _graph_icon(r: Rect, stroke: str, fill: str) -> str:
    x=r.x+34; y=r.cy; pts=[(x-18,y),(x+4,y-18),(x+22,y+10),(x-2,y+18)]
    edges=[(0,1),(1,2),(2,3),(3,0),(1,3)]
    parts=[f'<line x1="{pts[a][0]:.2f}" y1="{pts[a][1]:.2f}" x2="{pts[b][0]:.2f}" y2="{pts[b][1]:.2f}" stroke="{stroke}" stroke-width="1.2"/>' for a,b in edges]
    for i,(px,py) in enumerate(pts):
        parts.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="5.2" fill="{fill}" fill-opacity="{0.55+0.1*(i%3):.2f}" stroke="{stroke}" stroke-width="1"/>')
    return ''.join(parts)


def _document_icon(r: Rect, stroke: str, fill: str) -> str:
    x=r.x+18;y=r.cy-23;w=34;h=46
    return (f'<path d="M{x},{y} h{w-9} l9,9 v{h-9} h-{w} z" fill="{fill}" fill-opacity="0.5" stroke="{stroke}" stroke-width="1.2"/>'
            f'<path d="M{x+w-9},{y} v9 h9" fill="none" stroke="{stroke}" stroke-width="1.2"/>'
            f'<line x1="{x+7}" y1="{y+20}" x2="{x+w-7}" y2="{y+20}" stroke="{stroke}" stroke-width="1"/>'
            f'<line x1="{x+7}" y1="{y+29}" x2="{x+w-7}" y2="{y+29}" stroke="{stroke}" stroke-width="1"/>')


def _operator_icon(r: Rect, stroke: str, text: str) -> str:
    radius=min(r.width,r.height)*0.28
    return (f'<circle cx="{r.cx:.2f}" cy="{r.cy:.2f}" r="{radius:.2f}" fill="#FFFFFF" stroke="{stroke}" stroke-width="2"/>'
            + _text([text],r.cx,r.cy+radius*0.34,font_size=radius*1.15,fill=stroke,weight=700))


def _node_svg(node: ResolvedNode, family: str) -> str:
    r=node.rect; parts=[f'<g id="node-{_esc(node.id)}">']
    ntype=node.type.lower()
    if ntype in {"operator","add","multiply","gate"}:
        symbol={"add":"+","multiply":"×","gate":"σ"}.get(ntype,node.metadata.get("symbol","⊕"))
        parts.append(_operator_icon(r,node.stroke,str(symbol)))
        parts.append('</g>')
        return ''.join(parts)
    parts.append(_rounded_rect(r,node.fill,node.stroke,node.border_width,node.radius))
    icon_w=0
    if ntype in {"matrix","attention","mask","heatmap"}:
        parts.append(_matrix_icon(r,node.stroke,node.fill)); icon_w=58
    elif ntype in {"tensor","embedding","feature","stack"}:
        parts.append(_tensor_icon(r,node.stroke,node.fill)); icon_w=64
    elif ntype in {"vector","score","probability"}:
        parts.append(_vector_icon(r,node.stroke,node.fill)); icon_w=62
    elif ntype in {"graph","gcn","relation_graph","network"}:
        parts.append(_graph_icon(r,node.stroke,node.fill)); icon_w=70
    elif ntype in {"document","input","data","dataset","text"}:
        parts.append(_document_icon(r,node.stroke,node.fill)); icon_w=64
    tx=r.x+icon_w+(r.width-icon_w)/2
    text_w=r.width-icon_w-22
    label_lines=_wrap(node.label,text_w,node.font_size,max_lines=3)
    detail_lines=[]
    for d in node.details[:3]:
        detail_lines.extend(_wrap("• "+d,text_w,max(10,node.font_size-3),max_lines=1))
    dim_lines=[node.dimension] if node.dimension else []
    all_count=len(label_lines)+len(detail_lines)+len(dim_lines)
    line_h=node.font_size*1.18
    total_h=(len(label_lines)-1)*line_h + max(0,len(detail_lines))*max(11,node.font_size-3)*1.18 + (14 if dim_lines else 0)
    y=max(r.y+24,r.cy-total_h/2)
    parts.append(_text(label_lines,tx,y,font_size=node.font_size,fill=node.text_color,weight=node.font_weight,family=family))
    y+=max(1,len(label_lines))*line_h+3
    if detail_lines:
        parts.append(_text(detail_lines,tx,y,font_size=max(10,node.font_size-3),fill=node.text_color,weight=400,family=family,line_height=1.15))
        y+=len(detail_lines)*max(10,node.font_size-3)*1.15+2
    if dim_lines:
        parts.append(_text(dim_lines,tx,y,font_size=max(10,node.font_size-3),fill=node.stroke,weight=600,family="DejaVu Sans Mono, monospace",italic=True))
    if node.locked:
        parts.append(f'<circle cx="{r.right-13:.2f}" cy="{r.y+13:.2f}" r="6" fill="{node.stroke}"/><path d="M{r.right-16},{r.y+13} v-3 a3,3 0 0 1 6,0 v3" fill="none" stroke="#fff" stroke-width="1.2"/>')
    parts.append('</g>')
    return ''.join(parts)


def _edge_path(edge: ResolvedEdge, marker_id: str) -> str:
    pts=edge.points
    if len(pts)<2: return ''
    d=f'M {pts[0][0]:.2f},{pts[0][1]:.2f} '+' '.join(f'L {x:.2f},{y:.2f}' for x,y in pts[1:])
    dash=' stroke-dasharray="8 6"' if edge.dashed else ''
    marker=f' marker-end="url(#{marker_id})"' if edge.arrow in {'end','both'} else ''
    start_marker=f' marker-start="url(#{marker_id})"' if edge.arrow=='both' else ''
    return f'<path id="edge-{_esc(edge.id)}" d="{d}" fill="none" stroke="{edge.color}" stroke-width="{edge.width:.2f}" stroke-linejoin="round" stroke-linecap="round"{dash}{marker}{start_marker}/>'


def render_svg(fig: ResolvedFigure, output_path: str | Path, style: dict) -> Path:
    p=Path(output_path);p.parent.mkdir(parents=True,exist_ok=True)
    W,H=fig.canvas.width,fig.canvas.height
    family=style.get('font_family','Arial, sans-serif')
    title_family=style.get('title_font_family',family)
    edge_colors=sorted({e.color for e in fig.edges})
    parts=['<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<defs>']
    for color in edge_colors:
        mid=_hex_id(color)
        parts.append(f'<marker id="{mid}" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="{color}"/></marker>')
    parts.append('<filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="1" stdDeviation="1.5" flood-color="#64748B" flood-opacity="0.12"/></filter>')
    parts.append('</defs>')
    parts.append(f'<rect width="100%" height="100%" fill="{fig.canvas.background}"/>')
    parts.append(_text(_wrap(fig.title,W-160,34,max_lines=2),W/2,48,font_size=34,fill=style['text_primary'],weight=700,family=title_family))
    if fig.subtitle:
        parts.append(_text(_wrap(fig.subtitle,W-180,16,max_lines=2),W/2,74,font_size=15,fill=style['text_secondary'],weight=400,family=family,italic=True))
    # Groups first.
    for g in sorted(fig.groups,key=lambda x:x.order):
        parts.append(f'<g id="group-{_esc(g.id)}">')
        opacity=float(style.get('group_fill_opacity',0.35))
        parts.append(_rounded_rect(g.rect,g.fill,g.stroke,1.4,16,g.dashed,opacity))
        # Small title plate.
        title_w=min(g.rect.width-28,max(110,len(g.label)*8.2+28))
        tr=Rect(g.rect.x+14,g.rect.y+10,title_w,28)
        parts.append(_rounded_rect(tr,g.title_fill or g.fill,g.stroke,1.0,9,False,min(0.92,opacity+0.30)))
        parts.append(_text(_wrap(g.label,title_w-18,14,max_lines=1),tr.cx,tr.y+19,font_size=14,fill=style['text_primary'],weight=700,family=family))
        parts.append('</g>')
    # Edges before nodes.
    parts.append('<g id="edges">')
    for e in fig.edges:
        parts.append(_edge_path(e,_hex_id(e.color)))
        if e.label and len(e.points)>=2:
            mid=e.points[len(e.points)//2]
            label_lines=_wrap(e.label,160,12,max_lines=2)
            lw=max(60,max(len(x) for x in label_lines)*7+16)
            lh=18*len(label_lines)+6
            parts.append(_rounded_rect(Rect(mid[0]-lw/2,mid[1]-lh/2,lw,lh),'#FFFFFF','#CBD5E1',0.8,5,False,0.94))
            parts.append(_text(label_lines,mid[0],mid[1]-2,font_size=12,fill=style['text_secondary'],weight=500,family=family))
    parts.append('</g>')
    parts.append('<g id="nodes">')
    for n in fig.nodes:
        parts.append(_node_svg(n,family))
    parts.append('</g>')
    for a in fig.annotations:
        parts.append(f'<g id="annotation-{_esc(a.id)}">')
        parts.append(_rounded_rect(a.rect,a.fill,a.stroke,1.0,8,a.kind=='reference',0.94))
        lines=[]
        for raw in a.text.splitlines() or ['']:
            lines.extend(_wrap(raw,a.rect.width-22,a.font_size,max_lines=3))
        parts.append(_text(lines,a.rect.x+12,a.rect.y+20,font_size=a.font_size,fill=a.text_color,weight=400,anchor='start',family=family,line_height=1.18))
        parts.append('</g>')
    # Compact style label and footer.
    style_name=str(fig.metadata.get('style_name',fig.style_id))
    parts.append(_text([style_name],W-18,H-14,font_size=11,fill='#7B8794',weight=500,anchor='end',family=family,italic=True))
    parts.append('</svg>')
    p.write_text('\n'.join(parts),encoding='utf-8')
    return p
