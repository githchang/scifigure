from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .contact_sheet import make_contact_sheet
from .io import load_figure_ir, save_json
from .layout import resolve_layout
from .render_png import svg_to_png
from .render_svg import render_svg
from .render_vsdx import render_vsdx, validate_vsdx_package
from .routing import route_edges
from .style import STYLE_IDS, load_style
from .validate import ValidationError, validate_geometry, validate_ir


def _build(ir_path: Path, style_id: str, out_dir: Path, *, prefix: str, png_scale: float = 2.0, make_vsdx: bool = False) -> dict[str, Path]:
    ir=load_figure_ir(ir_path)
    validate_ir(ir)
    style=load_style(style_id)
    fig=resolve_layout(ir,style)
    route_edges(ir,fig,style)
    out_dir.mkdir(parents=True,exist_ok=True)
    resolved_path=save_json(out_dir/f'{prefix}.resolved.json',fig)
    validation=validate_geometry(fig)
    validation_path=save_json(out_dir/f'{prefix}.validation.json',validation)
    svg_path=render_svg(fig,out_dir/f'{prefix}.svg',style)
    png_path=svg_to_png(svg_path,out_dir/f'{prefix}.png',scale=png_scale)
    result={'resolved':resolved_path,'validation':validation_path,'svg':svg_path,'png':png_path}
    if make_vsdx:
        vsdx_path=render_vsdx(fig,out_dir/f'{prefix}.vsdx')
        package_report=validate_vsdx_package(vsdx_path)
        save_json(out_dir/f'{prefix}.vsdx_validation.json',package_report)
        if not package_report['valid']:
            raise RuntimeError('Generated VSDX package failed structural validation: '+str(package_report['errors']))
        result['vsdx']=vsdx_path
    return result


def cmd_validate(args: argparse.Namespace) -> int:
    ir=load_figure_ir(args.ir)
    report=validate_ir(ir)
    if args.output:
        save_json(args.output,report)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    ir_path=Path(args.ir)
    out=Path(args.output)
    styles=STYLE_IDS if args.styles=='all' else [x.strip() for x in args.styles.split(',') if x.strip()]
    unknown=[x for x in styles if x not in STYLE_IDS]
    if unknown:
        raise ValueError(f'Unknown styles: {unknown}')
    pngs=[]
    manifest={'ir':str(ir_path.resolve()),'styles':[]}
    for idx,style_id in enumerate(styles,1):
        style_out=out/style_id
        files=_build(ir_path,style_id,style_out,prefix='preview',png_scale=args.scale,make_vsdx=False)
        public_png=out/f'preview_{idx}_{style_id}.png'
        shutil.copy2(files['png'],public_png)
        pngs.append(public_png)
        manifest['styles'].append({'index':idx,'style_id':style_id,'preview':str(public_png),'working_svg':str(files['svg']),'resolved':str(files['resolved']),'validation':str(files['validation'])})
        if args.keep_svg:
            shutil.copy2(files['svg'],out/f'preview_{idx}_{style_id}.svg')
    save_json(out/'preview_manifest.json',manifest)
    if args.contact_sheet:
        make_contact_sheet(pngs,out/'preview_contact_sheet.png',columns=args.columns,thumb_width=args.thumb_width)
    print(f'Generated {len(pngs)} PNG previews in: {out}')
    for p in pngs: print(p)
    if args.contact_sheet: print(out/'preview_contact_sheet.png')
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    out=Path(args.output)
    files=_build(Path(args.ir),args.style,out,prefix=args.name,png_scale=args.scale,make_vsdx=args.vsdx)
    print(json.dumps({k:str(v) for k,v in files.items()},ensure_ascii=False,indent=2))
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    out=Path(args.output)
    working=out/'working'
    files=_build(Path(args.ir),args.style,working,prefix='figure_final',png_scale=args.scale,make_vsdx=True)
    final=out/'final';final.mkdir(parents=True,exist_ok=True)
    final_paths={}
    for key,ext in [('png','png'),('svg','svg'),('vsdx','vsdx')]:
        target=final/f'figure_final.{ext}'
        shutil.copy2(files[key],target)
        final_paths[key]=target
    report={
        'style_id':args.style,
        'outputs':{k:str(v) for k,v in final_paths.items()},
        'source_ir':str(Path(args.ir).resolve()),
        'resolved':str(files['resolved']),
        'geometry_validation':str(files['validation']),
        'vsdx_validation':str(working/'figure_final.vsdx_validation.json'),
    }
    save_json(final/'final_manifest.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0


def cmd_init_ir(args: argparse.Namespace) -> int:
    dst=Path(args.output)
    src=Path(__file__).resolve().parent.parent/'examples'/'demo_ir.json'
    if not src.exists():
        # Installed package: use importlib resources fallback.
        from importlib.resources import files
        src=Path(str(files('scifigure').joinpath('data','demo_ir.json')))
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
    print(dst)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog='scifigure',description='Deterministically render internal Figure IR into multi-style scientific figure previews and editable PNG/SVG/VSDX exports without external model APIs.')
    sub=p.add_subparsers(dest='command',required=True)
    v=sub.add_parser('validate-ir',help='Validate a Figure IR JSON file.')
    v.add_argument('--ir',required=True);v.add_argument('--output');v.set_defaults(func=cmd_validate)
    pr=sub.add_parser('preview',help='Generate six style PNG previews from one Figure IR.')
    pr.add_argument('--ir',required=True);pr.add_argument('--output',required=True)
    pr.add_argument('--styles',default='all',help='all or a comma-separated list of style IDs')
    pr.add_argument('--scale',type=float,default=2.0);pr.add_argument('--contact-sheet',action=argparse.BooleanOptionalAction,default=True)
    pr.add_argument('--columns',type=int,default=2);pr.add_argument('--thumb-width',type=int,default=760)
    pr.add_argument('--keep-svg',action='store_true',help='Expose candidate SVGs. The skill normally leaves them internal during preview.')
    pr.set_defaults(func=cmd_preview)
    r=sub.add_parser('render',help='Render one selected style to PNG/SVG and optionally VSDX.')
    r.add_argument('--ir',required=True);r.add_argument('--style',required=True,choices=STYLE_IDS);r.add_argument('--output',required=True)
    r.add_argument('--name',default='selected_preview');r.add_argument('--scale',type=float,default=2.0);r.add_argument('--vsdx',action='store_true')
    r.set_defaults(func=cmd_render)
    f=sub.add_parser('finalize',help='Generate final PNG, SVG, and editable VSDX from one selected style.')
    f.add_argument('--ir',required=True);f.add_argument('--style',required=True,choices=STYLE_IDS);f.add_argument('--output',required=True);f.add_argument('--scale',type=float,default=2.0)
    f.set_defaults(func=cmd_finalize)
    i=sub.add_parser('init-ir',help='Copy a developer example Figure IR for renderer testing; end users are not required to supply IR.')
    i.add_argument('--output',default='figure_ir.json');i.set_defaults(func=cmd_init_ir)
    return p


def main(argv: list[str] | None=None) -> int:
    parser=build_parser();args=parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (ValidationError,ValueError,RuntimeError,FileNotFoundError,json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
