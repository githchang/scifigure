from __future__ import annotations

from pathlib import Path


def svg_to_png(svg_path: str | Path, png_path: str | Path, *, scale: float = 2.0) -> Path:
    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError("CairoSVG is required for PNG preview generation. Install with: pip install cairosvg") from exc
    src=Path(svg_path); dst=Path(png_path); dst.parent.mkdir(parents=True,exist_ok=True)
    cairosvg.svg2png(url=str(src),write_to=str(dst),scale=scale)
    return dst
