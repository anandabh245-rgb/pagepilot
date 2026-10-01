import hashlib
from PIL import Image, ImageDraw, ImageFont

PAGE_NAME = "MUST WATCH"
TAGLINE = "ENTERTAINMENT NEWS"
SIZE = 1080
FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
PALETTES = [
    ((20, 20, 40), (120, 40, 160), (255, 190, 90)),
    ((15, 25, 45), (200, 50, 80), (255, 210, 120)),
    ((10, 30, 40), (30, 140, 170), (255, 220, 130)),
    ((35, 15, 30), (220, 120, 40), (255, 235, 160)),
    ((15, 15, 15), (190, 150, 40), (255, 255, 255)),
]


def font(size):
    for path in FONTS:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def make_card(headline, path):
    text = "".join(c for c in headline if ord(c) < 0x2600)
    text = " ".join(text.upper().split())[:110] or "ENTERTAINMENT NEWS"
    idx = int(hashlib.md5(text.encode()).hexdigest(), 16) % len(PALETTES)
    top, bottom, accent = PALETTES[idx]

    img = Image.new("RGB", (SIZE, SIZE), top)
    draw = ImageDraw.Draw(img)
    for y in range(SIZE):
        t = y / SIZE
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (SIZE, y)], fill=color)

    draw.text((80, 80), PAGE_NAME, font=font(46), fill=accent)
    draw.rectangle([80, 150, 280, 160], fill=accent)

    max_w, max_h = SIZE - 160, 640
    for size in range(120, 44, -6):
        fnt = font(size)
        lines = wrap(draw, text, fnt, max_w)
        line_h = int(size * 1.25)
        if len(lines) * line_h <= max_h:
            break
    y = 220 + (max_h - len(lines) * line_h) // 2
    for line in lines:
        draw.text((80, y), line, font=fnt, fill=(255, 255, 255))
        y += line_h

    draw.text((80, 960), TAGLINE, font=font(36), fill=accent)
    img.save(path, "PNG")
    return path
