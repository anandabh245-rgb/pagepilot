import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from card_maker import *

SERIF = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"]
COND = ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"] + FONTS
BOLD = FONTS


def font_from(paths, size):
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return font(size)


def fit(d, words, paths, box, hi_sizes=(150, 40), step=4, lh=1.12):
    x0, y0, x1, y1 = box
    for s in range(hi_sizes[0], hi_sizes[1] - 1, -step):
        f = font_from(paths, s)
        lines = layout(d, words, f, x1 - x0)
        if len(lines) * int(s * lh) <= (y1 - y0):
            return f, lines, int(s * lh)
    f = font_from(paths, hi_sizes[1])
    return f, layout(d, words, f, x1 - x0), int(hi_sizes[1] * lh)


def draw_block(d, words, paths, box, color, hi=None, hi_fill=None,
               hi_color=None, align="left", shadow=None, stroke=None,
               valign="top", sizes=(150, 40), lh=1.12):
    f, lines, line_h = fit(d, words, paths, box, sizes, lh=lh)
    x0, y0, x1, y1 = box
    total_h = len(lines) * line_h
    y = y0 + ((y1 - y0 - total_h) // 2 if valign == "middle" else 0)
    sp = d.textlength(" ", font=f)
    for line in lines:
        tw = sum(d.textlength(w, font=f) for _, w in line) + sp * (len(line) - 1)
        x = x0 if align == "left" else (x0 + (x1 - x0 - tw) / 2)
        for i, w in line:
            ww = d.textlength(w, font=f)
            if hi and i in hi and hi_fill:
                bb = d.textbbox((x, y), w, font=f)
                d.rounded_rectangle([bb[0] - 10, bb[1] - 6, bb[2] + 10, bb[3] + 6],
                                    radius=10, fill=hi_fill)
                d.text((x, y), w, font=f, fill=hi_color or (0, 0, 0))
            else:
                col = hi_color if (hi and i in hi and not hi_fill) else color
                if shadow:
                    d.text((x + 5, y + 6), w, font=f, fill=shadow)
                d.text((x, y), w, font=f, fill=col,
                       stroke_width=stroke[0] if stroke else 0,
                       stroke_fill=stroke[1] if stroke else None)
            x += ww + sp
        y += line_h
    return y


def grad_bg(top, bottom):
    img = Image.new("RGB", (SIZE, SIZE), top)
    d = ImageDraw.Draw(img)
    for y in range(SIZE):
        d.line([(0, y), (SIZE, y)], fill=lerp(top, bottom, y / SIZE))
    return img


def tint_gray(im, tint=(70, 60, 50)):
    a = im.split()[3]
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gray = im.convert("L")
    col = Image.merge("RGB", [gray.point(lambda v, t=t: int(v * t / 255 * 1.9)) for t in tint])
    g.paste(col, (0, 0))
    g.putalpha(a)
    return g


# ------------------------------------------------------------ 1. NEWS
def card_news(text, ctx, rnd):
    img = grad_bg((8, 16, 52), (0, 70, 150)).convert("RGBA")
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for r in range(120, 900, 110):
        od.ellipse([860 - r, 330 - r, 860 + r, 330 + r], outline=(120, 190, 255, 38), width=3)
    for i in range(-3, 9):
        od.polygon([(i * 160, 0), (i * 160 + 70, 0), (i * 160 - 250, SIZE), (i * 160 - 320, SIZE)],
                   fill=(255, 255, 255, 12))
    img = Image.alpha_composite(img, ov)
    img = glow(img, 860, 330, 230, (60, 160, 255), 120, 70)
    img = place(img, face_img(ctx["face"]), 850, 330, 300, 0)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    # top bar
    d.rectangle([0, 0, SIZE, 120], fill=(6, 10, 30))
    d.polygon([(0, 0), (470, 0), (430, 120), (0, 120)], fill=(214, 20, 40))
    d.ellipse([50, 44, 82, 76], fill=(255, 255, 255))
    d.text((100, 38), ctx["hook"], font=font_from(COND, 52), fill=(255, 255, 255))
    fh = font_from(COND, 50)
    hw = d.textlength(PAGE_NAME, font=fh)
    d.text((SIZE - 50 - hw, 36), PAGE_NAME, font=fh, fill=HOT)
    d.polygon(star_points(SIZE - 50 - hw - 40, 62, 22, 9), fill=HOT)
    d.rectangle([0, 120, SIZE, 128], fill=(214, 20, 40))
    # headline
    words = text.split()
    hi = pick_highlights(words)
    draw_block(d, words, COND, (60, 190, 700, 800), (255, 255, 255), hi=hi,
               hi_fill=HOT, hi_color=(10, 10, 30), shadow=(0, 0, 20),
               valign="middle", sizes=(128, 44), lh=1.1)
    d.rectangle([60, 810, 360, 822], fill=HOT)
    # lower third
    d.rectangle([0, 872, SIZE, 960], fill=(255, 255, 255))
    d.rectangle([0, 872, 250, 960], fill=(214, 20, 40))
    d.text((34, 892), "UPDATE", font=font_from(COND, 46), fill=(255, 255, 255))
    d.text((280, 890), ctx["label"] + "  |  " + PAGE_NAME, font=font_from(COND, 46),
           fill=(10, 20, 60))
    # ticker
    d.rectangle([0, 960, SIZE, SIZE], fill=(6, 10, 30))
    tick = ("  \u2605  " + PAGE_NAME + "  \u2605  FOLLOW FOR DAILY ENTERTAINMENT NEWS") * 3
    d.text((-30, 985), tick, font=font_from(COND, 40), fill=(255, 255, 255))
    return img


# ------------------------------------------------------------ 2. CHAT
REPLIES = {
    "shock": ["wait WHAT", "no way", "stop it"],
    "love": ["aww stop", "this is so cute", "I'm obsessed"],
    "laugh": ["I'm crying", "lol no way", "stoppp"],
    "star": ["wait what", "tell me more", "okay but why"],
}


def bubble(d, box, fill, r=44):
    d.rounded_rectangle(box, radius=r, fill=fill)


def card_chat(text, ctx, rnd):
    img = grad_bg((14, 14, 20), (28, 24, 44)).convert("RGBA")
    img = glow(img, 900, 160, 260, (255, 45, 120), 80, 90)
    img = glow(img, 120, 900, 240, (60, 160, 255), 70, 90)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, SIZE, 150], fill=(30, 30, 38))
    d.ellipse([40, 30, 130, 120], fill=HOT)
    d.polygon(star_points(85, 76, 30, 12), fill=(30, 20, 10))
    d.text((150, 36), PAGE_NAME + " GC", font=font_from(BOLD, 44), fill=(255, 255, 255))
    d.text((150, 92), "typing...", font=font_from(BOLD, 28), fill=(120, 200, 120))
    d.text((SIZE - 200, 52), "\u2022\u2022\u2022", font=font_from(BOLD, 50), fill=(180, 180, 190))
    gray, blue = (58, 58, 64), (10, 132, 255)
    f1 = font_from(BOLD, 42)
    # bubble 1 (friend)
    t1 = "did you see this??"
    w1 = int(d.textlength(t1, font=f1)) + 70
    bubble(d, [50, 190, 50 + w1, 280], gray)
    d.text((85, 211), t1, font=f1, fill=(255, 255, 255))
    # bubble 2 (headline, sent by me)
    words = text.split()
    hi = pick_highlights(words)
    f, lines, lh = fit(d, words, BOLD, (120, 330, 900, 560), (78, 40), 4, 1.12)
    sp = d.textlength(" ", font=f)
    tw = max(sum(d.textlength(w, font=f) for _, w in l) + sp * (len(l) - 1) for l in lines)
    th = len(lines) * lh
    x1 = SIZE - 50
    x0 = x1 - tw - 80
    bubble(d, [x0, 320, x1, 320 + th + 70], blue, 52)
    d.polygon([(x1 - 10, 320 + th + 30), (x1 + 14, 320 + th + 70), (x1 - 46, 320 + th + 66)], fill=blue)
    y = 352
    for line in lines:
        x = x0 + 40
        for i, w in line:
            col = HOT if i in hi else (255, 255, 255)
            d.text((x, y), w, font=f, fill=col)
            x += d.textlength(w, font=f) + sp
        y += lh
    base_y = 320 + th + 70
    # bubble 3 (friend reply)
    rep = REPLIES.get(ctx["face"], REPLIES["star"])[rnd.randint(0, 2)]
    f3 = font_from(BOLD, 56)
    w3 = int(d.textlength(rep, font=f3)) + 80
    by = base_y + 30
    bubble(d, [50, by, 50 + w3, by + 110], gray)
    d.text((90, by + 22), rep, font=f3, fill=(255, 255, 255))
    # sticker + typing bubble
    sy = by + 120
    img = img.convert("RGBA")
    img = place(img, face_img(ctx["face"]), 150, sy + 70, 170, -8)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    bubble(d, [270, sy + 30, 420, sy + 110], gray, 40)
    for k in range(3):
        d.ellipse([305 + k * 42, sy + 59, 329 + k * 42, sy + 83], fill=(170, 170, 178))
    # input bar
    d.rounded_rectangle([40, 960, SIZE - 40, 1040], radius=40, fill=(40, 40, 48))
    d.text((80, 978), "Follow " + PAGE_NAME + " for more", font=font_from(BOLD, 36), fill=(150, 150, 160))
    d.ellipse([SIZE - 125, 968, SIZE - 55, 1032], fill=blue)
    d.polygon([(SIZE - 100, 1000), (SIZE - 80, 986), (SIZE - 80, 1014)], fill=(255, 255, 255))
    return img


# ------------------------------------------------------------ 3. NEON
def neon(img, draw_fn, color, passes=((22, 2), (8, 1))):
    for blur, times in passes:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_fn(ImageDraw.Draw(layer), color + (255,))
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        for _ in range(times * 2):
            img = Image.alpha_composite(img, layer)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    core = lerp(color, (255, 255, 255), 0.75)
    draw_fn(ImageDraw.Draw(layer), core + (255,))
    return Image.alpha_composite(img, layer)


def card_neon(text, ctx, rnd):
    img = Image.new("RGB", (SIZE, SIZE), (9, 6, 20))
    d = ImageDraw.Draw(img)
    for y in range(0, SIZE, 54):
        off = 0 if (y // 54) % 2 == 0 else 54
        for x in range(-108, SIZE + 108, 108):
            d.rectangle([x + off, y, x + off + 104, y + 50], outline=(22, 16, 40), width=2)
    img = img.convert("RGBA")
    pink, cyan = (255, 40, 160), (40, 230, 255)
    img = glow(img, SIZE // 2, 540, 420, (120, 20, 160), 70, 120)
    words = text.split()
    hi = pick_highlights(words)
    f, lines, lh = fit(ImageDraw.Draw(img), words, BOLD, (110, 300, 970, 800), (110, 44), 4, 1.14)
    sp = ImageDraw.Draw(img).textlength(" ", font=f)
    tot = len(lines) * lh
    y0 = 300 + (500 - tot) // 2
    items = []
    for li, line in enumerate(lines):
        tw = sum(ImageDraw.Draw(img).textlength(w, font=f) for _, w in line) + sp * (len(line) - 1)
        x = (SIZE - tw) / 2
        for i, w in line:
            items.append((x, y0 + li * lh, w, cyan if i in hi else (255, 255, 255)))
            x += ImageDraw.Draw(img).textlength(w, font=f) + sp
    # frame
    def frame(dr, col):
        dr.rounded_rectangle([56, 56, SIZE - 56, SIZE - 56], radius=60, outline=col, width=10)
    img = neon(img, frame, pink)
    # header sign
    def head(dr, col):
        dr.text((SIZE // 2, 130), PAGE_NAME, font=font_from(BOLD, 96), fill=col, anchor="mm")
    img = neon(img, head, pink)
    def star(dr, col):
        for cx in (130, SIZE - 130):
            dr.polygon(star_points(cx, 130, 44, 18), outline=col, width=8)
    img = neon(img, star, cyan)
    # text lines, per word colour
    for colr in (cyan, (255, 255, 255)):
        sel = [it for it in items if it[3] == colr]
        if not sel:
            continue
        def txt(dr, col, sel=sel):
            for (x, y, w, _) in sel:
                dr.text((x, y), w, font=f, fill=col)
        base = colr if colr != (255, 255, 255) else (255, 190, 90)
        img = neon(img, txt, base)
    # bottom tag
    def tag(dr, col):
        dr.text((SIZE // 2, 870), ctx["label"], font=font_from(BOLD, 52), fill=col, anchor="mm")
        dr.line([(250, 925), (SIZE - 250, 925)], fill=col, width=8)
    img = neon(img, tag, cyan)
    def sub(dr, col):
        dr.text((SIZE // 2, 972), "FOLLOW FOR MORE", font=font_from(BOLD, 34), fill=col, anchor="mm")
    img = neon(img, sub, pink, passes=((10, 1),))
    return img.convert("RGB")


# ------------------------------------------------------------ 4. TABLOID
def card_tabloid(text, ctx, rnd):
    paper = (243, 231, 200)
    img = Image.new("RGB", (SIZE, SIZE), paper)
    d = ImageDraw.Draw(img)
    for _ in range(2600):
        x, y = rnd.randint(0, SIZE), rnd.randint(0, SIZE)
        c = rnd.randint(205, 232)
        d.point((x, y), fill=(c, c - 12, c - 40))
    ink = (24, 20, 16)
    red = (196, 22, 32)
    d.rectangle([40, 40, SIZE - 40, SIZE - 40], outline=ink, width=6)
    ms = 78
    while d.textlength("THE MUST WATCH TIMES", font=font_from(SERIF, ms)) > 940:
        ms -= 2
    d.text((SIZE // 2, 125), "THE MUST WATCH TIMES", font=font_from(SERIF, ms), fill=ink, anchor="mm")
    d.rectangle([60, 190, SIZE - 60, 196], fill=ink)
    d.rectangle([60, 204, SIZE - 60, 208], fill=ink)
    d.text((70, 218), "ENTERTAINMENT EDITION", font=font_from(BOLD, 28), fill=ink)
    d.text((SIZE - 70, 218), ctx["label"], font=font_from(BOLD, 28), fill=red, anchor="ra")
    d.rectangle([60, 262, SIZE - 60, 266], fill=ink)
    words = text.split()
    hi = pick_highlights(words)
    draw_block(d, words, SERIF, (70, 300, 690, 830), ink, hi=hi, hi_fill=red,
               hi_color=(255, 255, 255), valign="middle", sizes=(110, 44), lh=1.12)
    # photo frame with newsprint reaction
    d.rectangle([720, 300, 1010, 590], fill=(30, 26, 22))
    d.rectangle([730, 310, 1000, 580], fill=(222, 208, 176))
    img = img.convert("RGBA")
    face = tint_gray(face_img(ctx["face"]))
    img = place(img, face, 865, 445, 250, 0, shadow=False)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    d.text((865, 612), "THE REACTION OF THE DAY", font=font_from(BOLD, 22), fill=ink, anchor="ma")
    # stamp
    st = Image.new("RGBA", (420, 150), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([6, 6, 414, 144], radius=14, outline=red + (255,), width=10)
    sd.text((210, 75), ctx["hook"] if len(ctx["hook"]) < 12 else "EXCLUSIVE",
            font=font_from(BOLD, 56), fill=red + (255,), anchor="mm")
    st = st.rotate(12, expand=True, resample=Image.BICUBIC)
    img.paste(st, (610, 690), st)
    d = ImageDraw.Draw(img)
    # bottom strip + fake barcode
    d.rectangle([60, 880, SIZE - 60, 884], fill=ink)
    d.text((70, 905), "BY THE MUST WATCH DESK", font=font_from(BOLD, 30), fill=ink)
    d.text((70, 950), "FOLLOW FOR DAILY ENTERTAINMENT NEWS", font=font_from(BOLD, 30), fill=red)
    x = 800
    while x < 1000:
        w = rnd.choice([3, 5, 8])
        d.rectangle([x, 900, x + w, 985], fill=ink)
        x += w + rnd.choice([3, 5])
    return img
