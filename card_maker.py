import hashlib
import re
from PIL import Image, ImageDraw, ImageFont

PAGE_NAME = "MUST WATCH"
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
CATEGORIES = [
    ("TV NEWS", ["season", "series", "episode", "show", "netflix", "hbo",
                 "tv", "streaming", "reality", "cast", "premiere", "finale"]),
    ("MOVIE NEWS", ["movie", "film", "trailer", "box office", "oscar",
                    "sequel", "director", "cinema"]),
    ("MUSIC NEWS", ["album", "singer", "tour", "concert", "song", "band",
                    "grammy"]),
    ("CELEBRITY NEWS", ["star", "stars", "actor", "actress", "celebrity",
                        "couple", "wedding", "baby", "dating", "split"]),
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


def category(text):
    low = text.lower()
    tokens = set(re.findall(r"[a-z]+", low))
    for name, words in CATEGORIES:
        for w in words:
            if w in tokens or (" " in w and w in low):
                return name
    return "ENTERTAINMENT"


def layout(draw, words, fnt, max_w):
    space = draw.textlength(" ", font=fnt)
    lines, cur, cur_w = [], [], 0
    for i, w in enumerate(words):
        ww = draw.textlength(w, font=fnt)
        add = ww if not cur else space + ww
        if cur and cur_w + add > max_w:
            lines.append(cur)
            cur, cur_w = [(i, w)], ww
        else:
            cur.append((i, w))
            cur_w += add
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

    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([560, -280, 1320, 480], fill=accent + (45,))
    od.ellipse([-320, 680, 420, 1420], fill=(255, 255, 255, 20))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    draw.rectangle([28, 28, SIZE - 28, SIZE - 28], outline=accent, width=3)
    draw.text((80, 80), PAGE_NAME, font=font(46), fill=accent)

    chip = category(text)
    chip_font = font(32)
    chip_w = int(draw.textlength(chip, font=chip_font)) + 48
    x1 = SIZE - 80
    x0 = x1 - chip_w
    draw.rounded_rectangle([x0, 72, x1, 136], radius=32, fill=accent)
    draw.text((x0 + 24, 86), chip, font=chip_font, fill=top)

    words = text.split()
    max_w, max_h = SIZE - 160, 700
    for size in range(108, 47, -6):
        fnt = font(size)
        lines = layout(draw, words, fnt, max_w)
        line_h = int(size * 1.22)
        if len(lines) * line_h <= max_h:
            break
    space = draw.textlength(" ", font=fnt)
    y = 190 + (max_h - len(lines) * line_h) // 2
    for line in lines:
        x = 80
        for i, w in line:
            draw.text((x, y), w, font=fnt,
                      fill=accent if i < 2 else (255, 255, 255))
            x += draw.textlength(w, font=fnt) + space
        y += line_h

    draw.text((80, 955), "FOLLOW " + PAGE_NAME + " FOR MORE",
              font=font(34), fill=accent)
    img.save(path, "PNG")
    return path
