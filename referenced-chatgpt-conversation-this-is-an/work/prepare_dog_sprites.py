from pathlib import Path
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
SPRITES = OUTPUTS / "jack_russell_sprites"

SOURCE_IMAGES = {
    "idle_0.png": OUTPUTS / "dog_character.png",
    "walk_0.png": Path(r"C:\Users\Rafson\.codex\generated_images\01a029d3-c8b5-72c2-a69d-47bec58a777c\call_d878iHuSOGxCZ5qjxmfJD0vp.png"),
    "walk_1.png": Path(r"C:\Users\Rafson\.codex\generated_images\01a029d3-c8b5-72c2-a69d-47bec58a777c\call_CsrfbS3Jubbano3lQmdpFliT.png"),
    "jump_prepare_0.png": Path(r"C:\Users\Rafson\.codex\generated_images\01a029d3-c8b5-72c2-a69d-47bec58a777c\call_rgVr0XJd4R9No43YH50HbHnq.png"),
    "jump_0.png": Path(r"C:\Users\Rafson\.codex\generated_images\01a029d3-c8b5-72c2-a69d-47bec58a777c\call_L67yHoHE2L9AJraDuN1zWRae.png"),
    "fall_0.png": Path(r"C:\Users\Rafson\.codex\generated_images\01a029d3-c8b5-72c2-a69d-47bec58a777c\call_pLgzQbxfXinb1TciH2870WCt.png"),
    "land_0.png": Path(r"C:\Users\Rafson\.codex\generated_images\01a029d3-c8b5-72c2-a69d-47bec58a777c\call_5RQByl82WU5dGKaQmyCxp18B.png"),
    "crouch_0.png": Path(r"C:\Users\Rafson\.codex\generated_images\01a029d3-c8b5-72c2-a69d-47bec58a777c\call_6tt4LsFm8NFylBpAghqpAggM.png"),
    "look_up_0.png": Path(r"C:\Users\Rafson\.codex\generated_images\01a029d3-c8b5-72c2-a69d-47bec58a777c\call_IBZm5djcvX0ADoUvCLZGzpjM.png"),
    "bark_0.png": Path(r"C:\Users\Rafson\.codex\generated_images\01a029d3-c8b5-72c2-a69d-47bec58a777c\call_fvQnJ4G216LssnvHyeFDDPSj.png"),
    "bark_1.png": Path(r"C:\Users\Rafson\.codex\generated_images\01a029d3-c8b5-72c2-a69d-47bec58a777c\call_PIZuYGYc9ViPDkM9vbmhNnr8.png"),
}

CANVAS_SIZE = (112, 92)


def is_core_dog_pixel(pixel):
    r, g, b, a = pixel
    if a == 0:
        return False

    brightness = (r + g + b) / 3
    color_range = max(r, g, b) - min(r, g, b)
    is_white_fur = brightness > 135 and color_range < 95
    is_orange_fur = r > 115 and g > 45 and b < 95 and r > g * 1.12
    is_light_shadow = brightness > 95 and color_range < 55

    return is_white_fur or is_orange_fur or is_light_shadow


def is_near_body_detail(pixel):
    r, g, b, a = pixel
    if a == 0:
        return False

    brightness = (r + g + b) / 3
    color_range = max(r, g, b) - min(r, g, b)
    is_outline_or_feature = brightness < 95
    is_warm_edge = r > g > b and brightness < 140 and color_range >= 35
    is_paw_shadow = brightness < 155 and color_range < 70

    return is_outline_or_feature or is_warm_edge or is_paw_shadow


def remove_background(image):
    image = image.convert("RGBA")
    width, height = image.size
    source_pixels = image.load()

    core_mask = Image.new("L", image.size, 0)
    core_pixels = core_mask.load()
    for y in range(height):
        for x in range(width):
            if is_core_dog_pixel(source_pixels[x, y]):
                core_pixels[x, y] = 255

    body_area = core_mask.filter(ImageFilter.MaxFilter(21))
    detail_area = core_mask.filter(ImageFilter.MaxFilter(35))
    body_pixels = body_area.load()
    detail_pixels = detail_area.load()

    alpha = Image.new("L", image.size, 0)
    alpha_pixels = alpha.load()
    for y in range(height):
        for x in range(width):
            pixel = source_pixels[x, y]
            if body_pixels[x, y] and is_core_dog_pixel(pixel):
                alpha_pixels[x, y] = 255
            elif detail_pixels[x, y] and is_near_body_detail(pixel):
                alpha_pixels[x, y] = 255

    alpha = alpha.filter(ImageFilter.MaxFilter(3))
    image.putalpha(alpha)
    return image


def crop_and_center(image):
    bounds = image.getbbox()
    if not bounds:
        return Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))

    cropped = image.crop(bounds)
    cropped.thumbnail((CANVAS_SIZE[0] - 4, CANVAS_SIZE[1] - 4), Image.Resampling.NEAREST)

    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    x = (CANVAS_SIZE[0] - cropped.width) // 2
    y = CANVAS_SIZE[1] - cropped.height
    canvas.alpha_composite(cropped, (x, y))
    return canvas


def main():
    SPRITES.mkdir(parents=True, exist_ok=True)

    for output_name, source_path in SOURCE_IMAGES.items():
        image = Image.open(source_path)
        sprite = crop_and_center(remove_background(image))
        sprite.save(SPRITES / output_name)

    # Extra in-between frame made from the landing pose. This avoids ghosting
    # between different drawings while still giving a recovery beat.
    land = Image.open(SPRITES / "land_0.png").convert("RGBA")
    recovered = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    stretched = land.resize((106, 88), Image.Resampling.NEAREST)
    recovered.alpha_composite(stretched, (3, 4))
    recovered.save(SPRITES / "land_1.png")

    print(f"Sprites saved to {SPRITES}")


if __name__ == "__main__":
    main()
