#!/usr/bin/env python3
"""Make web-sized copies of the illustrations in ../drawings and write them to
site/public/illustrations. The originals are never modified. Re-run this whenever a
drawing changes:

    python pipeline/optimize_drawings.py

Expected files in drawings/:
    buildingBackground.png  the skyline (transparent sky)
    buildingLights.png      the lit windows, same canvas size as the skyline
    biker.png               the rider
    bikeDock.png            the Divvy dock with bikes
    bikeWheels.jpg          wheels reflected in water (full-bleed break before the map)
Optional: sun.png, skyNight.png, skyDay.png (see site/src/lib/illustrations.js)
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "drawings"
OUT = ROOT / "site" / "public" / "illustrations"
ALPHA_MIN = 8  # alpha above this counts as "drawn"


def opaque_box(im):
    a = np.array(im.getchannel("A"))
    ys, xs = np.where(a > ALPHA_MIN)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def save(im, name, width):
    height = round(im.height * width / im.width)
    im = im.resize((width, height), Image.LANCZOS)
    path = OUT / name
    im.save(path, "WEBP", quality=90, method=6)
    print(f"  {name:20s} {width}x{height}  {path.stat().st_size / 1024:6.0f} KB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # The skyline and its lights share one canvas. Crop both to the same rows, so they stay
    # aligned: from just above the tallest drawn pixel in either layer to the bottom edge.
    sky = Image.open(SRC / "buildingBackground.png").convert("RGBA")
    lights = Image.open(SRC / "buildingLights.png").convert("RGBA")
    assert sky.size == lights.size, f"skyline {sky.size} and lights {lights.size} must match"
    top = max(0, min(opaque_box(sky)[1], opaque_box(lights)[1]) - 40)
    box = (0, top, sky.width, sky.height)
    print(f"skyline + lights, cropped to rows {top}-{sky.height}")
    save(sky.crop(box), "skyline.webp", 2400)
    save(lights.crop(box), "skyline-lit.webp", 2400)

    # The rider: trim the empty margin so the wheels sit on the bottom edge.
    biker = Image.open(SRC / "biker.png").convert("RGBA")
    x0, y0, x1, y1 = opaque_box(biker)
    pad = 24
    box = (max(0, x0 - pad), max(0, y0 - pad), min(biker.width, x1 + pad), y1)
    print(f"biker, cropped to {box}")
    save(biker.crop(box), "foreground.webp", 1100)

    # The dock: trim empty margin like the rider; accept either file name.
    for name in ("bikeDock.png", "divvyDock.png", "dock.png"):
        if (SRC / name).exists():
            dock = Image.open(SRC / name).convert("RGBA")
            x0, y0, x1, y1 = opaque_box(dock)
            pad = 24
            box = (max(0, x0 - pad), max(0, y0 - pad), min(dock.width, x1 + pad), min(dock.height, y1 + pad))
            print(f"{name}, cropped to {tuple(int(v) for v in box)}")
            save(dock.crop(box), "dock.webp", 1300)
            break

    # The wheels are a full-bleed picture with no transparency (a JPG or PNG).
    for name in ("bikeWheels.jpg", "bikeWheels.png"):
        if (SRC / name).exists():
            print(name)
            save(Image.open(SRC / name).convert("RGB"), "wheels.webp", 2400)
            break

    # The sun: crop to a square centered on the drawn disc, so the page can place it exactly
    # on the point the glow is centered on.
    if (SRC / "sun.png").exists():
        sun = Image.open(SRC / "sun.png").convert("RGBA")
        x0, y0, x1, y1 = opaque_box(sun)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        half = max(x1 - x0, y1 - y0) / 2 + 12
        box = (round(cx - half), round(cy - half), round(cx + half), round(cy + half))
        canvas = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0))
        canvas.alpha_composite(sun.crop((max(0, box[0]), max(0, box[1]), min(sun.width, box[2]), min(sun.height, box[3]))),
                               (max(0, -box[0]), max(0, -box[1])))
        print("sun.png")
        save(canvas, "sun.webp", 700)

    for name, out, width in [("skyNight.png", "sky-night.webp", 2000),
                             ("skyDay.png", "sky-day.webp", 2000)]:
        if (SRC / name).exists():
            print(name)
            save(Image.open(SRC / name).convert("RGBA"), out, width)


if __name__ == "__main__":
    main()
