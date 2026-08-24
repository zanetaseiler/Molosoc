#!/usr/bin/env python3
"""
Builds a labeled grid contact sheet from a list of rendered post images —
the standard "here's the whole batch at a glance" deliverable to hand back
for approval alongside the individual PNGs and the manifest.

Usage:
    python contact_sheet.py out.png img1.png img2.png img3.png ... \
        [--cols 5] [--thumb-width 200] [--labels "001,002,003,..."] \
        [--font /path/to/a/font.ttf] [--font-size 12]

If --labels is omitted, each image's filename stem is used as its label.
Images may have transparent corners (e.g. from a rounded-corner render) —
they're composited onto a white background before thumbnailing so corners
don't show as black.

Row height adapts per row to each row's tallest thumbnail (useful when a
set mixes portrait ratios), so don't assume every thumbnail is the same
height when placing labels below it.
"""
import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def flatten_to_white(im):
    im = im.convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    return bg.convert('RGB')


def build_contact_sheet(image_paths, labels, out_path, cols=5, thumb_width=200, pad=14, label_h=20, font_path=None, font_size=12):
    n = len(image_paths)
    rows = math.ceil(n / cols)
    cell_w = thumb_width + pad

    thumbs = []
    for p in image_paths:
        im = flatten_to_white(Image.open(p))
        th = int(thumb_width * im.height / im.width)
        thumbs.append(im.resize((thumb_width, th)))

    row_heights = []
    for r in range(rows):
        chunk = thumbs[r * cols:(r + 1) * cols]
        row_heights.append(max((t.height for t in chunk), default=0))
    cell_hs = [h + label_h + pad for h in row_heights]

    sheet_w = pad + cols * cell_w
    sheet_h = pad + sum(cell_hs) + 20
    sheet = Image.new('RGB', (sheet_w, sheet_h), '#FFFFFF')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()

    y_cursor = pad
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            if idx >= n:
                continue
            x = pad + c * cell_w
            thumb = thumbs[idx]
            sheet.paste(thumb, (x, y_cursor))
            draw.text((x, y_cursor + thumb.height + 3), labels[idx], fill='#171719', font=font)
        y_cursor += cell_hs[r]

    sheet.save(out_path)
    return sheet.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out_path')
    ap.add_argument('images', nargs='+')
    ap.add_argument('--cols', type=int, default=5)
    ap.add_argument('--thumb-width', type=int, default=200)
    ap.add_argument('--labels', default=None, help='Comma-separated labels, same order as images. Defaults to filename stems.')
    ap.add_argument('--font', default=None, help='Path to a .ttf for labels; falls back to a basic default font.')
    ap.add_argument('--font-size', type=int, default=12)
    args = ap.parse_args()

    labels = args.labels.split(',') if args.labels else [Path(p).stem for p in args.images]
    if len(labels) != len(args.images):
        raise SystemExit(f'{len(labels)} labels but {len(args.images)} images — must match 1:1.')

    size = build_contact_sheet(
        args.images, labels, args.out_path,
        cols=args.cols, thumb_width=args.thumb_width,
        font_path=args.font, font_size=args.font_size,
    )
    print(f'{args.out_path}: {size[0]}x{size[1]}, {len(args.images)} images')


if __name__ == '__main__':
    main()
