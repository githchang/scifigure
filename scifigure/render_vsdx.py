from __future__ import annotations

import datetime as _dt
import math
import xml.sax.saxutils as sax
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .models import Rect, ResolvedEdge, ResolvedFigure, ResolvedNode

NS='http://schemas.microsoft.com/office/visio/2012/main'
RNS='http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def _x(v: object) -> str:
    return sax.escape(str(v), {'"':'&quot;'})


def _f(v: float) -> str:
    return f'{v:.6f}'.rstrip('0').rstrip('.') or '0'


def _inch(px: float, scale: float) -> float:
    return px/scale


def _screen_rect_to_visio(r: Rect, canvas_h: float, scale: float) -> tuple[float,float,float,float]:
    w=_inch(r.width,scale); h=_inch(r.height,scale)
    pinx=_inch(r.cx,scale)
    piny=_inch(canvas_h-r.cy,scale)
    return pinx,piny,w,h


def _character_section(font_size_px: float, color: str, bold: bool=False, font_name: str='Arial') -> str:
    size=max(0.09,font_size_px/72.0)
    style=1 if bold else 0
    return (f'<Section N="Character"><Row IX="0"><Cell N="Font" V="0"/><Cell N="Color" V="{_x(color)}"/>'
            f'<Cell N="Size" V="{_f(size)}"/><Cell N="Style" V="{style}"/><Cell N="Case" V="0"/>'
            f'<Cell N="Pos" V="0"/><Cell N="FontScale" V="1"/></Row></Section>')


def _paragraph_section(align: int=1) -> str:
    return (f'<Section N="Paragraph"><Row IX="0"><Cell N="IndFirst" V="0"/><Cell N="IndLeft" V="0"/>'
            f'<Cell N="IndRight" V="0"/><Cell N="SpLine" V="-1"/><Cell N="SpBefore" V="0"/>'
            f'<Cell N="SpAfter" V="0"/><Cell N="HorzAlign" V="{align}"/></Row></Section>')


def _text_block_section() -> str:
    return ('<Section N="TextBlock"><Row IX="0"><Cell N="LeftMargin" V="0.08"/><Cell N="RightMargin" V="0.08"/>'
            '<Cell N="TopMargin" V="0.05"/><Cell N="BottomMargin" V="0.05"/><Cell N="VerticalAlign" V="1"/>'
            '<Cell N="DefaultTabStop" V="0.5"/><Cell N="TextBkgnd" V="0"/></Row></Section>')


def _rect_geometry(w: float,h: float) -> str:
    return (f'<Section N="Geometry" IX="0"><Cell N="NoFill" V="0"/><Cell N="NoLine" V="0"/>'
            f'<Row T="MoveTo" IX="1"><Cell N="X" V="0"/><Cell N="Y" V="0"/></Row>'
            f'<Row T="LineTo" IX="2"><Cell N="X" V="{_f(w)}"/><Cell N="Y" V="0"/></Row>'
            f'<Row T="LineTo" IX="3"><Cell N="X" V="{_f(w)}"/><Cell N="Y" V="{_f(h)}"/></Row>'
            f'<Row T="LineTo" IX="4"><Cell N="X" V="0"/><Cell N="Y" V="{_f(h)}"/></Row>'
            f'<Row T="LineTo" IX="5"><Cell N="X" V="0"/><Cell N="Y" V="0"/></Row></Section>')


def _ellipse_geometry(w: float,h: float) -> str:
    # Ellipse row is supported by Visio and LibreOffice's VSDX importer.
    return (f'<Section N="Geometry" IX="0"><Row T="Ellipse" IX="1">'
            f'<Cell N="X" V="{_f(w/2)}"/><Cell N="Y" V="{_f(h/2)}"/>'
            f'<Cell N="A" V="{_f(w)}"/><Cell N="B" V="{_f(h/2)}"/>'
            f'<Cell N="C" V="{_f(w/2)}"/><Cell N="D" V="{_f(h)}"/></Row></Section>')


def _shape_xml(shape_id: int, name: str, r: Rect, canvas_h: float, scale: float, *, fill: str, stroke: str,
               line_width_px: float=1.5, text: str='', text_color: str='#111111', font_size: float=16,
               bold: bool=False, radius_px: float=8, ellipse: bool=False, dashed: bool=False) -> str:
    pinx,piny,w,h=_screen_rect_to_visio(r,canvas_h,scale)
    dash=2 if dashed else 1
    geom=_ellipse_geometry(w,h) if ellipse else _rect_geometry(w,h)
    return (f'<Shape ID="{shape_id}" NameU="{_x(name)}" Name="{_x(name)}" Type="Shape">'
            f'<Cell N="PinX" V="{_f(pinx)}"/><Cell N="PinY" V="{_f(piny)}"/>'
            f'<Cell N="Width" V="{_f(w)}"/><Cell N="Height" V="{_f(h)}"/>'
            f'<Cell N="LocPinX" V="{_f(w/2)}"/><Cell N="LocPinY" V="{_f(h/2)}"/><Cell N="Angle" V="0"/>'
            f'<Cell N="FillForegnd" V="{_x(fill)}"/><Cell N="FillPattern" V="1"/>'
            f'<Cell N="LineColor" V="{_x(stroke)}"/><Cell N="LineWeight" V="{_f(max(0.006,line_width_px/100.0))}"/>'
            f'<Cell N="LinePattern" V="{dash}"/><Cell N="Rounding" V="{_f(max(0,radius_px/scale))}"/>'
            f'{_character_section(font_size,text_color,bold)}{_paragraph_section(1)}{_text_block_section()}{geom}'
            f'<Text>{_x(text)}</Text></Shape>')


def _line_shape_xml(shape_id: int, name: str, edge: ResolvedEdge, canvas_h: float, scale: float) -> str:
    pts=edge.points
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    minx,maxx=min(xs),max(xs); miny,maxy=min(ys),max(ys)
    # Keep a nonzero local coordinate space.
    if maxx-minx < 1: maxx=minx+1
    if maxy-miny < 1: maxy=miny+1
    r=Rect(minx,miny,maxx-minx,maxy-miny)
    pinx,piny,w,h=_screen_rect_to_visio(r,canvas_h,scale)
    rows=[]
    for i,(gx,gy) in enumerate(pts,1):
        lx=_inch(gx-minx,scale)
        ly=_inch(maxy-gy,scale)
        typ='MoveTo' if i==1 else 'LineTo'
        rows.append(f'<Row T="{typ}" IX="{i}"><Cell N="X" V="{_f(lx)}"/><Cell N="Y" V="{_f(ly)}"/></Row>')
    dash=2 if edge.dashed else 1
    end_arrow=13 if edge.arrow in {'end','both'} else 0
    begin_arrow=13 if edge.arrow=='both' else 0
    geom='<Section N="Geometry" IX="0"><Cell N="NoFill" V="1"/><Cell N="NoLine" V="0"/>'+''.join(rows)+'</Section>'
    text=edge.label or ''
    return (f'<Shape ID="{shape_id}" NameU="{_x(name)}" Name="{_x(name)}" Type="Shape">'
            f'<Cell N="PinX" V="{_f(pinx)}"/><Cell N="PinY" V="{_f(piny)}"/>'
            f'<Cell N="Width" V="{_f(w)}"/><Cell N="Height" V="{_f(h)}"/>'
            f'<Cell N="LocPinX" V="{_f(w/2)}"/><Cell N="LocPinY" V="{_f(h/2)}"/><Cell N="Angle" V="0"/>'
            f'<Cell N="FillPattern" V="0"/><Cell N="LineColor" V="{_x(edge.color)}"/>'
            f'<Cell N="LineWeight" V="{_f(max(0.008,edge.width/100.0))}"/><Cell N="LinePattern" V="{dash}"/>'
            f'<Cell N="BeginArrow" V="{begin_arrow}"/><Cell N="EndArrow" V="{end_arrow}"/>'
            f'{_character_section(11,"#44505E",False)}{_paragraph_section(1)}{_text_block_section()}{geom}'
            f'<Text>{_x(text)}</Text></Shape>')


def _node_text(n: ResolvedNode) -> str:
    lines=[n.label]
    lines.extend('• '+d for d in n.details[:3])
    if n.dimension: lines.append(n.dimension)
    return '\n'.join(lines)


def _page_xml(fig: ResolvedFigure, scale: float) -> str:
    shapes=[]; connects=[]; sid=1
    id_map={}
    # Background groups are ordinary editable shapes at the bottom of z-order.
    for g in sorted(fig.groups,key=lambda x:x.order):
        shapes.append(_shape_xml(sid,f'Group_{g.id}',g.rect,fig.canvas.height,scale,fill=g.fill,stroke=g.stroke,
                                 line_width_px=1.2,text=g.label,text_color='#334155',font_size=13,bold=True,
                                 radius_px=14,dashed=g.dashed))
        sid+=1
    # Connectors behind nodes. They are editable vector line shapes, not raster images.
    for e in fig.edges:
        edge_sid=sid
        shapes.append(_line_shape_xml(sid,f'Edge_{e.id}',e,fig.canvas.height,scale));sid+=1
        # Connections are included as semantic glue records. The shapes remain movable/editable.
        connects.append((edge_sid,e.source,e.target))
    for n in fig.nodes:
        id_map[n.id]=sid
        ellipse=n.type.lower() in {'operator','add','multiply','gate'}
        text=_node_text(n)
        if ellipse:
            text={'add':'+','multiply':'×','gate':'σ'}.get(n.type.lower(),str(n.metadata.get('symbol','⊕')))
        shapes.append(_shape_xml(sid,f'Node_{n.id}',n.rect,fig.canvas.height,scale,fill=n.fill,stroke=n.stroke,
                                 line_width_px=n.border_width,text=text,text_color=n.text_color,font_size=n.font_size,
                                 bold=True,radius_px=n.radius,ellipse=ellipse,dashed=False))
        sid+=1
    for a in fig.annotations:
        shapes.append(_shape_xml(sid,f'Annotation_{a.id}',a.rect,fig.canvas.height,scale,fill=a.fill,stroke=a.stroke,
                                 line_width_px=1.0,text=a.text,text_color=a.text_color,font_size=a.font_size,bold=False,
                                 radius_px=7,dashed=a.kind=='reference'))
        sid+=1
    connect_xml=[]
    for edge_sid,src,target in connects:
        if src in id_map:
            connect_xml.append(f'<Connect FromSheet="{edge_sid}" FromCell="BeginX" ToSheet="{id_map[src]}" ToCell="PinX"/>')
        if target in id_map:
            connect_xml.append(f'<Connect FromSheet="{edge_sid}" FromCell="EndX" ToSheet="{id_map[target]}" ToCell="PinX"/>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<PageContents xmlns="{NS}"><Shapes>{"".join(shapes)}</Shapes>'
            f'<Connects>{"".join(connect_xml)}</Connects></PageContents>')


def render_vsdx(fig: ResolvedFigure, output_path: str | Path) -> Path:
    out=Path(output_path);out.parent.mkdir(parents=True,exist_ok=True)
    # 100 pixels per inch keeps a 1600x900 canvas as a 16x9 inch editable page.
    scale=100.0
    page_w=fig.canvas.width/scale;page_h=fig.canvas.height/scale
    now=_dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
    files={
    '[Content_Types].xml':f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/visio/document.xml" ContentType="application/vnd.ms-visio.drawing.main+xml"/>
<Override PartName="/visio/pages/pages.xml" ContentType="application/vnd.ms-visio.pages+xml"/>
<Override PartName="/visio/pages/page1.xml" ContentType="application/vnd.ms-visio.page+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>''',
    '_rels/.rels':'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/document" Target="visio/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>''',
    'docProps/core.xml':f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>{_x(fig.title)}</dc:title><dc:creator>SciFigure</dc:creator><cp:lastModifiedBy>SciFigure</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>''',
    'docProps/app.xml':'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>SciFigure</Application><AppVersion>1.0</AppVersion></Properties>''',
    'visio/document.xml':f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<VisioDocument xmlns="{NS}" xmlns:r="{RNS}"><DocumentSettings DefaultTextStyle="0" DefaultLineStyle="0" DefaultFillStyle="0" DefaultGuideStyle="0"/><Colors/><FaceNames><FaceName ID="0" Name="Arial" UnicodeRanges="-1" CharSets="0" Panos="2 11 6 4 2 2 2 2 2 4" Flags="325"/></FaceNames><StyleSheets><StyleSheet ID="0" NameU="No Style" Name="No Style" IsCustomName="1" IsCustomNameU="1"/></StyleSheets><Pages r:id="rId1"/></VisioDocument>''',
    'visio/_rels/document.xml.rels':'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/pages" Target="pages/pages.xml"/></Relationships>''',
    'visio/pages/pages.xml':f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Pages xmlns="{NS}" xmlns:r="{RNS}"><Page ID="0" Name="Page-1" NameU="Page-1"><PageSheet><Cell N="PageWidth" V="{_f(page_w)}"/><Cell N="PageHeight" V="{_f(page_h)}"/><Cell N="DrawingScale" V="1"/><Cell N="PageScale" V="1"/><Cell N="DrawingSizeType" V="0"/><Cell N="DrawingScaleType" V="0"/><Cell N="InhibitSnap" V="0"/></PageSheet><Rel r:id="rId1"/></Page></Pages>''',
    'visio/pages/_rels/pages.xml.rels':'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/page" Target="page1.xml"/></Relationships>''',
    'visio/pages/page1.xml':_page_xml(fig,scale),
    }
    with ZipFile(out,'w',ZIP_DEFLATED) as z:
        for name,content in files.items(): z.writestr(name,content)
    return out


def validate_vsdx_package(path: str | Path) -> dict[str, object]:
    from xml.etree import ElementTree as ET
    p=Path(path)
    required={'[Content_Types].xml','_rels/.rels','visio/document.xml','visio/_rels/document.xml.rels','visio/pages/pages.xml','visio/pages/_rels/pages.xml.rels','visio/pages/page1.xml'}
    errors=[]
    with ZipFile(p,'r') as z:
        names=set(z.namelist())
        missing=sorted(required-names)
        if missing: errors.append(f'missing package parts: {missing}')
        for name in required & names:
            try: ET.fromstring(z.read(name))
            except Exception as exc: errors.append(f'{name}: invalid XML: {exc}')
    return {'valid':not errors,'errors':errors,'file':str(p),'size':p.stat().st_size}
