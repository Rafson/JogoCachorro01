from __future__ import annotations

import json
import math
import shutil
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "jack_russell_sprites"
DOG = OUT / "dog"
SHEETS = OUT / "spritesheets"
PREVIEW = OUT / "preview"
ZIP_PATH = ROOT / "outputs" / "jack_russell_64x64_sprites.zip"

FRAME = 64

ANIMATIONS = {
    "idle": 4,
    "walk": 6,
    "run": 8,
    "jump": 4,
    "fall": 3,
    "land": 3,
    "sit": 4,
    "lay": 4,
    "wake_up": 4,
    "hit": 4,
    "death": 6,
    "victory": 6,
}

COLORS = {
    "outline": (45, 35, 28, 255),
    "white": (244, 240, 226, 255),
    "shadow": (194, 184, 166, 255),
    "tan": (176, 113, 58, 255),
    "dark_tan": (118, 71, 38, 255),
    "nose": (28, 24, 22, 255),
    "pink": (224, 128, 130, 255),
    "red": (225, 68, 61, 255),
}


def px(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], color: tuple[int, int, int, int]) -> None:
    draw.rectangle(xy, fill=color)


def ellipse(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], color: tuple[int, int, int, int]) -> None:
    draw.ellipse(xy, fill=color)


def line(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], color: tuple[int, int, int, int], width: int = 2) -> None:
    draw.line(points, fill=color, width=width)


def leg(draw: ImageDraw.ImageDraw, x: int, y: int, pose: int, front: bool = True) -> None:
    o = COLORS["outline"]
    w = COLORS["white"]
    s = COLORS["shadow"]
    if pose == 0:
        px(draw, (x, y, x + 4, y + 13), o)
        px(draw, (x + 1, y, x + 3, y + 12), w)
        px(draw, (x - 1, y + 12, x + 6, y + 15), o)
        px(draw, (x, y + 12, x + 5, y + 14), w)
    elif pose == 1:
        px(draw, (x, y, x + 4, y + 8), o)
        px(draw, (x + 1, y, x + 3, y + 7), w)
        px(draw, (x + 3, y + 7, x + 10, y + 11), o)
        px(draw, (x + 4, y + 7, x + 9, y + 10), w)
        px(draw, (x + 8, y + 10, x + 14, y + 13), o)
        px(draw, (x + 9, y + 10, x + 13, y + 12), w)
    elif pose == 2:
        px(draw, (x, y, x + 4, y + 8), o)
        px(draw, (x + 1, y, x + 3, y + 7), w)
        px(draw, (x - 6, y + 7, x + 2, y + 11), o)
        px(draw, (x - 5, y + 7, x + 1, y + 10), w)
        px(draw, (x - 11, y + 10, x - 4, y + 13), o)
        px(draw, (x - 10, y + 10, x - 5, y + 12), w)
    else:
        px(draw, (x, y, x + 4, y + 10), o)
        px(draw, (x + 1, y, x + 3, y + 9), s if not front else w)
        px(draw, (x + 1, y + 9, x + 8, y + 12), o)
        px(draw, (x + 2, y + 9, x + 7, y + 11), w)


def draw_dog(
    img: Image.Image,
    *,
    x: int = 12,
    y: int = 23,
    bob: int = 0,
    stretch: int = 0,
    tail_angle: int = 0,
    ear: int = 0,
    leg_poses: tuple[int, int, int, int] = (0, 0, 0, 0),
    head_dx: int = 0,
    head_dy: int = 0,
    sit: float = 0.0,
    lay: float = 0.0,
    hit: bool = False,
    dead: bool = False,
    victory: float = 0.0,
) -> None:
    d = ImageDraw.Draw(img)
    o = COLORS["outline"]
    w = COLORS["white"]
    s = COLORS["shadow"]
    tan = COLORS["tan"]
    dark = COLORS["dark_tan"]
    nose = COLORS["nose"]
    pink = COLORS["pink"]
    red = COLORS["red"]

    y += bob
    if lay > 0:
        y += int(10 * lay)
    if sit > 0:
        y += int(6 * sit)

    body_y = y + int(2 * sit)
    body_h = max(10, 18 - int(5 * lay) - int(2 * sit) + stretch)
    body_w = 26 + int(3 * lay)
    body_x = x + int(2 * lay)

    if not dead:
        if tail_angle > 0:
            line(d, [(body_x + 2, body_y + 6), (body_x - 4, body_y + 1), (body_x - 7, body_y - 3)], o, 3)
            line(d, [(body_x + 2, body_y + 6), (body_x - 4, body_y + 1), (body_x - 7, body_y - 3)], w, 1)
        elif tail_angle < 0:
            line(d, [(body_x + 2, body_y + 8), (body_x - 5, body_y + 12), (body_x - 8, body_y + 15)], o, 3)
            line(d, [(body_x + 2, body_y + 8), (body_x - 5, body_y + 12), (body_x - 8, body_y + 15)], w, 1)
        else:
            line(d, [(body_x + 2, body_y + 7), (body_x - 6, body_y + 6), (body_x - 9, body_y + 4)], o, 3)
            line(d, [(body_x + 2, body_y + 7), (body_x - 6, body_y + 6), (body_x - 9, body_y + 4)], w, 1)

    ellipse(d, (body_x, body_y, body_x + body_w, body_y + body_h), o)
    ellipse(d, (body_x + 2, body_y + 2, body_x + body_w - 2, body_y + body_h - 2), w)
    ellipse(d, (body_x + 8, body_y + 3, body_x + 19, body_y + 13), tan)
    px(d, (body_x + body_w - 8, body_y + body_h - 5, body_x + body_w - 2, body_y + body_h - 2), s)

    if dead:
        px(d, (body_x + 6, body_y + body_h - 1, body_x + body_w + 12, body_y + body_h + 6), o)
        px(d, (body_x + 7, body_y + body_h, body_x + body_w + 11, body_y + body_h + 5), w)
    elif lay > 0.65:
        px(d, (body_x + 4, body_y + body_h - 1, body_x + 28, body_y + body_h + 3), o)
        px(d, (body_x + 5, body_y + body_h, body_x + 27, body_y + body_h + 2), w)
        px(d, (body_x + 18, body_y + body_h - 2, body_x + 42, body_y + body_h + 2), o)
        px(d, (body_x + 19, body_y + body_h - 1, body_x + 41, body_y + body_h + 1), w)
    else:
        ly = body_y + body_h - 2
        xs = [body_x + 7, body_x + 15, body_x + body_w - 10, body_x + body_w - 3]
        for i, lx in enumerate(xs):
            leg(d, lx, ly - (2 if sit > 0 and i < 2 else 0), leg_poses[i], front=i >= 2)

    neck_x = body_x + body_w - 4
    neck_y = body_y + 3
    px(d, (neck_x - 2, neck_y + 3, neck_x + 4, neck_y + 14), o)
    px(d, (neck_x - 1, neck_y + 4, neck_x + 3, neck_y + 13), w)

    hx = body_x + body_w + 1 + head_dx - int(8 * lay)
    hy = body_y - 5 + head_dy + int(2 * lay)
    if dead:
        hy += 12
        hx -= 1
    if sit > 0:
        hy -= int(3 * sit)
        hx -= int(2 * sit)

    ellipse(d, (hx, hy + 3, hx + 17, hy + 18), o)
    ellipse(d, (hx + 1, hy + 4, hx + 16, hy + 17), w)
    px(d, (hx + 10, hy + 8, hx + 19, hy + 14), o)
    px(d, (hx + 11, hy + 9, hx + 18, hy + 13), w)
    px(d, (hx + 18, hy + 10, hx + 21, hy + 13), nose)
    ellipse(d, (hx + 5, hy + 6, hx + 12, hy + 13), tan)
    if dead:
        line(d, [(hx + 12, hy + 7), (hx + 15, hy + 10)], nose, 1)
        line(d, [(hx + 15, hy + 7), (hx + 12, hy + 10)], nose, 1)
    else:
        px(d, (hx + 13, hy + 8, hx + 14, hy + 9), nose)
    px(d, (hx + 17, hy + 14, hx + 19, hy + 16), pink if hit else o)

    if ear >= 0:
        px(d, (hx + 2, hy, hx + 9, hy + 8), o)
        px(d, (hx + 3, hy + 1, hx + 8, hy + 7), tan)
        px(d, (hx + 5, hy + 7 + ear, hx + 10, hy + 13 + ear), o)
        px(d, (hx + 6, hy + 7 + ear, hx + 9, hy + 12 + ear), dark)
    else:
        px(d, (hx + 1, hy + 1, hx + 10, hy + 5), o)
        px(d, (hx + 2, hy + 2, hx + 9, hy + 4), tan)

    if hit:
        px(d, (hx + 21, hy + 6, hx + 22, hy + 8), red)
        px(d, (body_x - 7, body_y - 5, body_x - 3, body_y - 2), red)

    if victory > 0:
        px(d, (hx + 7, hy - 6, hx + 11, hy - 1), o)
        px(d, (hx + 8, hy - 5, hx + 10, hy - 2), w)
        px(d, (hx + 12, hy - 9, hx + 14, hy - 7), red)
        px(d, (hx + 16, hy - 8, hx + 18, hy - 6), tan)


def frame_params(anim: str, i: int, n: int) -> dict:
    phase = i / n
    wave = math.sin(phase * math.tau)
    alt = i % 2

    if anim == "idle":
        return {"bob": 1 if i in (1, 2) else 0, "tail_angle": [0, 1, 0, -1][i], "ear": [0, 1, 0, 0][i]}
    if anim == "walk":
        poses = [(0, 1, 2, 0), (1, 0, 0, 2), (0, 2, 1, 0), (2, 0, 0, 1), (0, 1, 2, 0), (1, 0, 0, 2)]
        return {"bob": 1 if alt else 0, "tail_angle": 1 if alt else 0, "leg_poses": poses[i]}
    if anim == "run":
        poses = [(1, 2, 1, 2), (3, 3, 0, 0), (2, 1, 2, 1), (0, 0, 3, 3)] * 2
        return {"bob": -1 if i in (1, 5) else 1 if i in (3, 7) else 0, "stretch": 1 if i in (1, 5) else -1, "tail_angle": 1, "leg_poses": poses[i], "head_dx": 1}
    if anim == "jump":
        return [
            {"bob": 5, "stretch": -2, "leg_poses": (3, 3, 3, 3), "tail_angle": -1},
            {"bob": -2, "stretch": 1, "leg_poses": (2, 2, 1, 1), "tail_angle": 1, "head_dy": -1},
            {"bob": -7, "stretch": 1, "leg_poses": (2, 1, 1, 2), "tail_angle": 1, "head_dy": -1},
            {"bob": -5, "stretch": 0, "leg_poses": (0, 2, 2, 0), "tail_angle": 0},
        ][i]
    if anim == "fall":
        return [
            {"bob": -3, "leg_poses": (0, 2, 2, 0), "tail_angle": 0},
            {"bob": 0, "leg_poses": (3, 2, 2, 3), "tail_angle": -1, "head_dy": 1},
            {"bob": 3, "leg_poses": (3, 3, 3, 3), "tail_angle": -1, "head_dy": 2},
        ][i]
    if anim == "land":
        return [
            {"bob": 5, "stretch": -3, "leg_poses": (3, 3, 3, 3), "tail_angle": -1, "head_dy": 2},
            {"bob": 2, "stretch": -1, "leg_poses": (0, 0, 0, 0), "tail_angle": 0},
            {"bob": 0, "stretch": 0, "leg_poses": (0, 0, 0, 0), "tail_angle": 1},
        ][i]
    if anim == "sit":
        return {"sit": min(1, i / 3), "leg_poses": (3, 3, 0, 0), "tail_angle": [-1, -1, 0, 0][i], "head_dy": -1 if i == 3 else 0}
    if anim == "lay":
        return {"lay": min(1, i / 3), "leg_poses": (3, 3, 3, 3), "tail_angle": -1, "head_dy": i}
    if anim == "wake_up":
        lays = [1.0, 0.75, 0.35, 0.0]
        return {"lay": lays[i], "leg_poses": (3, 3, 0, 0), "tail_angle": 0 if i > 1 else -1, "head_dy": 2 - i}
    if anim == "hit":
        return {"bob": [0, -2, 1, 0][i], "head_dx": [-1, -3, -1, 0][i], "head_dy": [0, 1, 0, 0][i], "leg_poses": (3, 2, 3, 2), "tail_angle": -1, "hit": i in (1, 2)}
    if anim == "death":
        return {"lay": min(1, i / 4), "dead": i >= 3, "hit": i < 2, "tail_angle": -1, "head_dy": i // 2}
    if anim == "victory":
        return {"bob": -1 if alt else 0, "tail_angle": 1, "ear": alt, "leg_poses": (0, 1 if alt else 0, 0, 2 if alt else 0), "victory": 1.0}
    return {}


def make_frame(anim: str, i: int, n: int) -> Image.Image:
    img = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    draw_dog(img, **frame_params(anim, i, n))
    return img


def write_outputs() -> dict:
    if OUT.exists():
        shutil.rmtree(OUT)
    DOG.mkdir(parents=True, exist_ok=True)
    SHEETS.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)

    manifest = {
        "frame_width": FRAME,
        "frame_height": FRAME,
        "background": "transparent",
        "direction": "side_profile_facing_right",
        "animations": {},
    }

    all_preview_rows = []
    for anim, count in ANIMATIONS.items():
        folder = DOG / anim
        folder.mkdir(parents=True, exist_ok=True)
        frames = []
        for i in range(count):
            frame = make_frame(anim, i, count)
            filename = f"{anim}_{i:02d}.png"
            frame.save(folder / filename)
            frames.append(frame)

        sheet = Image.new("RGBA", (FRAME * count, FRAME), (0, 0, 0, 0))
        for i, frame in enumerate(frames):
            sheet.alpha_composite(frame, (i * FRAME, 0))
        sheet.save(SHEETS / f"{anim}.png")

        manifest["animations"][anim] = {
            "frame_count": count,
            "folder": f"dog/{anim}",
            "spritesheet": f"spritesheets/{anim}.png",
            "frames": [f"{anim}_{i:02d}.png" for i in range(count)],
        }
        all_preview_rows.append((anim, sheet))

    margin = 18
    label_h = 14
    preview_w = max(sheet.width for _, sheet in all_preview_rows) + margin * 2
    preview_h = sum(label_h + FRAME + 8 for _ in all_preview_rows) + margin
    preview = Image.new("RGBA", (preview_w, preview_h), (38, 42, 48, 255))
    d = ImageDraw.Draw(preview)
    y = margin
    for anim, sheet in all_preview_rows:
        d.text((margin, y), anim, fill=(242, 242, 242, 255))
        y += label_h
        preview.alpha_composite(checker(sheet), (margin, y))
        y += FRAME + 8
    preview.save(PREVIEW / "all_animations_preview.png")

    with (OUT / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    (OUT / "README.txt").write_text(
        "\n".join(
            [
                "Jack Russell Terrier pixel art sprites",
                "",
                "All individual frames are 64x64 PNG files with transparent background.",
                "The dog faces right in every animation.",
                "",
                "Folders:",
                "- dog/<animation>/<animation>_00.png ... individual frames",
                "- spritesheets/<animation>.png ... one horizontal spritesheet per animation",
                "- manifest.json ... frame size, frame counts, and file names",
                "- preview/all_animations_preview.png ... quick visual review sheet",
                "",
                "Animations included:",
                ", ".join(ANIMATIONS.keys()),
                "",
            ]
        ),
        encoding="utf-8",
    )

    validate_outputs()
    make_zip()
    return manifest


def checker(img: Image.Image) -> Image.Image:
    bg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(bg)
    for yy in range(0, img.height, 8):
        for xx in range(0, img.width, 8):
            c = (88, 94, 102, 255) if ((xx // 8 + yy // 8) % 2) else (67, 72, 80, 255)
            px(d, (xx, yy, xx + 7, yy + 7), c)
    bg.alpha_composite(img)
    return bg


def validate_outputs() -> None:
    problems = []
    for path in sorted(DOG.glob("*/*.png")):
        img = Image.open(path).convert("RGBA")
        if img.size != (FRAME, FRAME):
            problems.append(f"{path}: size {img.size}")
            continue
        bbox = img.getchannel("A").getbbox()
        if not bbox:
            problems.append(f"{path}: empty frame")
            continue
        left, top, right, bottom = bbox
        if left <= 0 or top <= 0 or right >= FRAME or bottom >= FRAME:
            problems.append(f"{path}: artwork touches frame edge bbox={bbox}")
    if problems:
        raise RuntimeError("\n".join(problems))


def make_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(OUT.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(OUT.parent))


if __name__ == "__main__":
    write_outputs()
    print(f"Wrote {OUT}")
    print(f"Wrote {ZIP_PATH}")
