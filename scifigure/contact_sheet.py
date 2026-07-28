from __future__ import annotations

from pathlib import Path


def make_contact_sheet(image_paths: list[str | Path], output_path: str | Path, *, columns: int = 2, thumb_width: int = 900) -> Path:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Pillow is required for contact sheet generation. Install with: pip install pillow") from exc
    paths=[Path(p) for p in image_paths]
    images=[Image.open(p).convert('RGB') for p in paths]
    thumbs=[]
    for img in images:
        h=round(img.height*thumb_width/img.width)
        thumbs.append(img.resize((thumb_width,h)))
    gap=28; label_h=42
    rows=(len(thumbs)+columns-1)//columns
    cell_h=max(im.height for im in thumbs)+label_h
    canvas=Image.new('RGB',(columns*thumb_width+(columns+1)*gap,rows*cell_h+(rows+1)*gap),'white')
    draw=ImageDraw.Draw(canvas)
    for i,(im,path) in enumerate(zip(thumbs,paths)):
        c=i%columns;r=i//columns
        x=gap+c*(thumb_width+gap);y=gap+r*cell_h
        draw.rounded_rectangle((x-3,y-3,x+im.width+3,y+im.height+3),radius=10,outline='#CBD5E1',width=2)
        canvas.paste(im,(x,y))
        draw.text((x+8,y+im.height+10),path.stem,fill='#334155')
    out=Path(output_path);out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out,quality=95)
    return out
