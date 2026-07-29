from __future__ import annotations

from pathlib import Path


def make_contact_sheet(
    image_paths: list[str | Path],
    output_path: str | Path,
    *,
    columns: int = 2,
    thumb_width: int = 900,
) -> Path:
    try:
        from PIL import Image, ImageDraw, ImageEnhance
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required for contact sheet generation. Install with: pip install pillow"
        ) from exc

    paths = [Path(path) for path in image_paths]
    images = [Image.open(path).convert("RGB") for path in paths]

    # Small nearest-neighbour thumbnails made the previous total preview look
    # washed out and jagged. Force a readable width and use Lanczos resampling.
    thumb_width = max(960, int(thumb_width))
    thumbs = []
    for image in images:
        height = round(image.height * thumb_width / image.width)
        resized = image.resize((thumb_width, height), Image.Resampling.LANCZOS)
        resized = ImageEnhance.Sharpness(resized).enhance(1.08)
        thumbs.append(resized)

    gap = 34
    label_height = 46
    rows = (len(thumbs) + columns - 1) // columns
    cell_height = max(image.height for image in thumbs) + label_height
    canvas = Image.new(
        "RGB",
        (columns * thumb_width + (columns + 1) * gap, rows * cell_height + (rows + 1) * gap),
        "white",
    )
    draw = ImageDraw.Draw(canvas)

    for index, (image, path) in enumerate(zip(thumbs, paths)):
        column = index % columns
        row = index // columns
        x = gap + column * (thumb_width + gap)
        y = gap + row * cell_height
        draw.rounded_rectangle(
            (x - 4, y - 4, x + image.width + 4, y + image.height + 4),
            radius=12,
            outline="#94A3B8",
            width=2,
            fill="#FFFFFF",
        )
        canvas.paste(image, (x, y))
        draw.text((x + 10, y + image.height + 12), path.stem, fill="#1F2937")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=98, subsampling=0)
    return output
