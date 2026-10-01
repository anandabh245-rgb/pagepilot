import hashlib
import math
import random
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PAGE_NAME = "MUST WATCH"
SIZE = 1080
FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
HOT = (255, 214, 10)
DARK = (22, 10, 36)

LABELS = [
    ("TV NEWS", ["season", "series", "episode", "show", "netflix", "hbo",
                 "tv", "streaming", "reality", "cast", "premiere", "finale",
                 "traitors", "link"]),
    ("MOVIE NEWS", ["movie", "film", "trailer", "box", "oscar", "sequel",
                    "director", "cinema"]),
    ("MUSIC NEWS", ["album", "singer", "tour", "concert", "song", "band",
                    "grammy"]),
    ("CELEBRITY NEWS", ["star", "stars", "actor", "actress", "celebrity",
                        "couple", "wedding", "baby", "dating", "split"]),
]
HOOKS = [
    (["reveal", "revealed", "reveals"], "REVEALED"),
    (["trailer"], "NEW TRAILER"),
    (["returns", "return", "comeback", "back"], "COMEBACK"),
    (["cast", "casting"], "CAST NEWS"),
    (["finale"], "FINALE"),
    (["premiere"], "PREMIERE"),
]
LOVE = {"love", "wedding", "couple", "engaged", "engagement", "baby",
        "dating", "married", "romance", "relationship", "kiss"}
SHOCK = {"shock", "shocking", "secret", "twist", "exposed", "feud", "split",
         "fight", "drama", "truth", "scandal", "betrayal", "traitors",
         "leak", "leaked", "controversy", "backlash", "fans"}
LAUGH = {"funny", "hilarious", "comedy", "laugh", "joke", "parody", "roast",
         "meme", "fun", "prank", "laughs"}
BOOST = {"NEW", "REVEALED", "REVEALS", "FINALLY", "RETURNS", "TRAILER",
         "SEASON", "CAST", "FINALE", "PREMIERE", "SECRET", "TWIST", "NOT"}
STOP = {"IS", "THE", "A", "AN", "OF", "TO", "IN", "ON", "AND", "FOR", "WITH",
        "AT", "BY", "FROM", "AS", "ITS", "ARE", "BE", "HAS", "HAVE", "WILL",
        "THIS", "THAT", "WE", "OUR", "YOUR", "WHO", "HOW", "WHY"}
SOMBER_RE = re.compile(
    r"\b(passed away|dies|died|dead at|death of|rip|in memoriam|"
    r"remembering|we lost|we've lost|stars lost|mourn\w*|funeral)\b")
SPACE_RE = re.compile(
    r"\b(space|galaxy|alien\w*|mars|moon|astronaut\w*|sci-fi|star wars|"
    r"star trek|dune|nasa|planet\w*|cosmic|universe)\b")


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


def star_points(cx, cy, r_out, r_in, n=5, rot=-90):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def heart(d, cx, cy, s, fill, outline=None):
    pts = []
    for i in range(0, 360, 4):
        t = math.radians(i)
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t)
              - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * s, cy + (y - 2.5) * s))
    d.polygon(pts, fill=fill, outline=outline)


def canvas(n=400):
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- stickers
def grin(d):
    d.chord([100, 170, 300, 340], 0, 180, fill=(255, 255, 255),
            outline=(90, 30, 10), width=6)
    d.chord([114, 214, 286, 334], 0, 180, fill=(110, 25, 25))
    d.chord([150, 290, 250, 340], 0, 180, fill=(235, 90, 110))


def face_img(kind):
    im, d = canvas()
    if kind == "alien":
        for i in range(190, 0, -2):
            d.ellipse([200 - i, 200 - i, 200 + i, 200 + i],
                      fill=lerp((90, 190, 70), (170, 240, 120), 1 - i / 190))
        d.ellipse([10, 10, 390, 390], outline=(40, 110, 40), width=8)
        d.polygon([(70, 140), (190, 190), (165, 255), (95, 225)],
                  fill=(15, 20, 15))
        d.polygon([(330, 140), (210, 190), (235, 255), (305, 225)],
                  fill=(15, 20, 15))
        d.ellipse([110, 175, 135, 200], fill=(255, 255, 255))
        d.ellipse([268, 175, 293, 200], fill=(255, 255, 255))
        d.arc([160, 280, 240, 330], 20, 160, fill=(30, 80, 30), width=8)
        return im
    for i in range(190, 0, -2):
        d.ellipse([200 - i, 200 - i, 200 + i, 200 + i],
                  fill=lerp((255, 168, 10), (255, 238, 110), 1 - i / 190))
    d.ellipse([10, 10, 390, 390], outline=(205, 115, 0), width=8)
    brown = (70, 35, 10)
    if kind == "star":
        for cx in (135, 265):
            d.polygon(star_points(cx, 160, 56, 23), fill=(240, 55, 75),
                      outline=(130, 20, 35))
        grin(d)
    elif kind == "love":
        for cx in (135, 265):
            heart(d, cx, 165, 3.4, (235, 40, 70), (130, 15, 35))
            d.ellipse([cx - 28, 130, cx - 12, 146], fill=(255, 190, 200))
        grin(d)
    elif kind == "laugh":
        for cx in (135, 265):
            d.arc([cx - 45, 125, cx + 45, 205], 200, 340, fill=brown, width=16)
        grin(d)
        for x0 in (60, 300):
            d.ellipse([x0, 190, x0 + 42, 255], fill=(120, 205, 255),
                      outline=(40, 120, 200), width=4)
    else:  # shock
        for cx in (135, 265):
            d.ellipse([cx - 46, 115, cx + 46, 207], fill=(255, 255, 255),
                      outline=brown, width=7)
            d.ellipse([cx - 18, 145, cx + 18, 181], fill=(25, 15, 10))
            d.ellipse([cx - 10, 150, cx - 1, 160], fill=(255, 255, 255))
        d.arc([88, 55, 182, 115], 200, 340, fill=brown, width=14)
        d.arc([218, 55, 312, 115], 200, 340, fill=brown, width=14)
        d.ellipse([160, 245, 240, 345], fill=(110, 25, 25),
                  outline=(90, 30, 10), width=6)
        d.ellipse([178, 300, 222, 335], fill=(235, 90, 110))
    return im


def popcorn():
    im, d = canvas()
    for (x, y, r) in [(120, 150, 46), (190, 110, 52), (265, 140, 48),
                      (150, 95, 40), (235, 85, 40), (95, 185, 36),
                      (300, 180, 36), (200, 170, 50)]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 245, 210),
                  outline=(225, 180, 80), width=5)
        d.ellipse([x - r * .5, y - r * .1, x + r * .1, y + r * .5],
                  fill=(255, 224, 150))
    top = (95, 305)
    bot = (122, 278)
    for i in range(6):
        col = (225, 35, 50) if i % 2 == 0 else (255, 255, 255)
        x0t = top[0] + (top[1] - top[0]) * i / 6
        x1t = top[0] + (top[1] - top[0]) * (i + 1) / 6
        x0b = bot[0] + (bot[1] - bot[0]) * i / 6
        x1b = bot[0] + (bot[1] - bot[0]) * (i + 1) / 6
        d.polygon([(x0t, 195), (x1t, 195), (x1b, 385), (x0b, 385)], fill=col)
    d.line([(95, 195), (122, 385), (278, 385), (305, 195)],
           fill=(120, 15, 25), width=6, joint="curve")
    d.rounded_rectangle([85, 182, 315, 210], radius=12, fill=(225, 35, 50),
                        outline=(120, 15, 25), width=6)
    return im


def clapper():
    im, d = canvas()
    d.rounded_rectangle([55, 175, 345, 355], radius=14, fill=(32, 32, 44),
                        outline=(0, 0, 0), width=6)
    for y in (215, 255, 295):
        d.rounded_rectangle([85, y, 190, y + 14], radius=6,
                            fill=(255, 255, 255))
        d.rounded_rectangle([210, y, 300, y + 14], radius=6,
                            fill=(255, 214, 10))

    def bar(w, h):
        b = Image.new("RGBA", (w, h), (20, 20, 28, 255))
        bd = ImageDraw.Draw(b)
        for i in range(-2, 9):
            bd.polygon([(i * 56, 0), (i * 56 + 28, 0), (i * 56 + 8, h),
                        (i * 56 - 20, h)], fill=(255, 255, 255, 255))
        ImageDraw.Draw(b).rectangle([0, 0, w - 1, h - 1], outline=(0, 0, 0),
                                    width=5)
        return b
    im.paste(bar(290, 40), (55, 140))
    arm = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    arm.paste(bar(290, 40), (55, 100))
    arm = arm.rotate(16, center=(55, 120), resample=Image.BICUBIC)
    im = Image.alpha_composite(im, arm)
    return im


def flash():
    im, d = canvas()
    d.polygon(star_points(200, 200, 190, 100, n=12, rot=-90),
              fill=(255, 240, 120), outline=(255, 160, 0))
    d.polygon(star_points(200, 200, 140, 74, n=12, rot=-75),
              fill=(255, 255, 255))
    return im


def trophy():
    im, d = canvas()
    gold, dk = (255, 200, 40), (190, 120, 0)
    d.arc([40, 80, 160, 200], 90, 270, fill=dk, width=22)
    d.arc([240, 80, 360, 200], 270, 90, fill=dk, width=22)
    d.polygon([(110, 70), (290, 70), (268, 200), (232, 258), (168, 258),
               (132, 200)], fill=gold, outline=dk)
    d.polygon([(125, 80), (165, 80), (160, 205), (150, 205)],
              fill=(255, 235, 140))
    d.rounded_rectangle([100, 55, 300, 90], radius=12, fill=gold, outline=dk,
                        width=5)
    d.rectangle([182, 258, 218, 305], fill=dk)
    d.rounded_rectangle([130, 305, 270, 350], radius=10, fill=gold,
                        outline=dk, width=5)
    d.rounded_rectangle([105, 350, 295, 380], radius=8, fill=dk)
    d.polygon(star_points(200, 150, 42, 18), fill=(255, 245, 170),
              outline=dk)
    return im


def mic():
    im, d = canvas()
    d.polygon([(168, 195), (232, 195), (220, 360), (180, 360)],
              fill=(45, 45, 58), outline=(0, 0, 0))
    head = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    hd = ImageDraw.Draw(head)
    hd.ellipse([105, 40, 295, 230], fill=(200, 205, 215))
    for k in range(-4, 6):
        hd.line([(105 + k * 28, 70), (195 + k * 28, 215)],
                fill=(120, 125, 140), width=5)
        hd.line([(295 - k * 28, 70), (205 - k * 28, 215)],
                fill=(120, 125, 140), width=5)
    mask = Image.new("L", (400, 400), 0)
    ImageDraw.Draw(mask).ellipse([105, 40, 295, 230], fill=255)
    im.paste(head, (0, 0), mask)
    d = ImageDraw.Draw(im)
    d.ellipse([105, 40, 295, 230], outline=(30, 30, 40), width=7)
    d.rounded_rectangle([150, 215, 250, 245], radius=10, fill=(255, 214, 10),
                        outline=(30, 30, 40), width=5)
    return im


def heart_st():
    im, d = canvas()
    heart(d, 200, 200, 11.5, (235, 40, 70), (130, 15, 35))
    d.ellipse([105, 105, 160, 160], fill=(255, 150, 165))
    return im


def star_st():
    im, d = canvas()
    d.polygon(star_points(200, 208, 190, 80), fill=(255, 205, 40),
              outline=(200, 120, 0))
    d.polygon(star_points(200, 208, 120, 50), fill=(255, 235, 130))
    return im


def planet(c_dark, c_light, ring=True):
    im, d = canvas()
    if ring:
        back = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
        ImageDraw.Draw(back).ellipse([10, 140, 390, 260],
                                     outline=(250, 220, 150), width=22)
        im = Image.alpha_composite(im, back.rotate(-22, resample=Image.BICUBIC))
    d = ImageDraw.Draw(im)
    for i in range(130, 0, -2):
        off = (130 - i) * 0.3
        d.ellipse([200 - i - off, 200 - i - off, 200 + i - off,
                   200 + i - off], fill=lerp(c_dark, c_light, 1 - i / 130))
    d.arc([90, 150, 310, 230], 200, 340, fill=lerp(c_dark, c_light, .6), width=10)
    d.arc([95, 200, 305, 280], 20, 160, fill=lerp(c_dark, c_light, .3), width=10)
    if ring:
        front = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
        ImageDraw.Draw(front).arc([10, 140, 390, 260], 0, 180,
                                  fill=(250, 220, 150), width=22)
        im = Image.alpha_composite(im, front.rotate(-22, resample=Image.BICUBIC))
    return im


def rocket():
    im, d = canvas()
    d.polygon([(160, 255), (240, 255), (200, 385)], fill=(255, 130, 20))
    d.polygon([(178, 255), (222, 255), (200, 335)], fill=(255, 225, 90))
    d.polygon([(140, 190), (70, 285), (148, 255)], fill=(225, 40, 60),
              outline=(100, 10, 20))
    d.polygon([(260, 190), (330, 285), (252, 255)], fill=(225, 40, 60),
              outline=(100, 10, 20))
    d.polygon([(200, 20), (246, 80), (262, 160), (258, 258), (142, 258),
               (138, 160), (154, 80)], fill=(240, 242, 250),
              outline=(40, 40, 70))
    d.polygon([(200, 20), (246, 80), (154, 80)], fill=(225, 40, 60),
              outline=(100, 10, 20))
    d.ellipse([165, 125, 235, 195], fill=(90, 170, 255), outline=(40, 40, 70),
              width=7)
    d.ellipse([178, 138, 198, 158], fill=(200, 230, 255))
    return im


def moon():
    im, d = canvas()
    m = Image.new("L", (400, 400), 0)
    md = ImageDraw.Draw(m)
    md.ellipse([30, 30, 370, 370], fill=255)
    md.ellipse([110, 10, 450, 350], fill=0)
    col = Image.new("RGBA", (400, 400), (255, 238, 165, 255))
    im.paste(col, (0, 0), m)
    ImageDraw.Draw(im).ellipse([90, 230, 130, 270], fill=(235, 215, 140))
    ImageDraw.Draw(im).ellipse([60, 150, 85, 175], fill=(235, 215, 140))
    return im


def candle():
    im, d = canvas()
    d.ellipse([55, 322, 345, 385], fill=(190, 150, 60), outline=(120, 85, 20),
              width=5)
    d.ellipse([85, 322, 315, 365], fill=(225, 185, 90))
    d.rounded_rectangle([148, 150, 252, 352], radius=10, fill=(250, 240, 215))
    d.rectangle([218, 152, 250, 350], fill=(232, 216, 182))
    d.ellipse([148, 136, 252, 168], fill=(255, 249, 232),
              outline=(210, 195, 160), width=3)
    d.rounded_rectangle([156, 152, 180, 222], radius=11, fill=(255, 251, 238))
    d.line([(200, 142), (200, 112)], fill=(40, 30, 25), width=6)
    d.ellipse([166, 40, 234, 128], fill=(255, 150, 30))
    d.polygon([(166, 88), (234, 88), (200, 0)], fill=(255, 150, 30))
    d.ellipse([181, 66, 219, 124], fill=(255, 220, 80))
    d.polygon([(181, 94), (219, 94), (200, 28)], fill=(255, 220, 80))
    d.ellipse([192, 86, 208, 120], fill=(255, 255, 240))
    return im


def lily():
    im, d = canvas()
    green, dg = (60, 140, 70), (30, 90, 40)
    d.line([(200, 230), (200, 395)], fill=green, width=18)
    d.polygon([(200, 340), (110, 300), (95, 350), (200, 370)], fill=green,
              outline=dg)
    d.polygon([(200, 320), (290, 280), (305, 335), (200, 355)], fill=green,
              outline=dg)
    cx, cy = 200, 160
    for k in range(6):
        a = math.radians(-90 + 60 * k)
        tip = (cx + 150 * math.cos(a), cy + 150 * math.sin(a))
        l = (cx + 70 * math.cos(a - .5), cy + 70 * math.sin(a - .5))
        r = (cx + 70 * math.cos(a + .5), cy + 70 * math.sin(a + .5))
        d.polygon([(cx, cy), l, tip, r], fill=(252, 252, 248),
                  outline=(195, 195, 210))
        mid = (cx + 85 * math.cos(a), cy + 85 * math.sin(a))
        d.line([(cx, cy), mid], fill=(225, 220, 238), width=7)
    for k in range(5):
        a = math.radians(-80 + 40 * k)
        e = (cx + 52 * math.cos(a), cy + 52 * math.sin(a))
        d.line([(cx, cy), e], fill=(150, 100, 30), width=4)
        d.ellipse([e[0] - 8, e[1] - 8, e[0] + 8, e[1] + 8], fill=(235, 170, 40))
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(250, 220, 90))
    return im


def bow():
    im, d = canvas()
    blk, hi = (14, 14, 18), (70, 70, 80)
    for ang in (-18, 18):
        loop = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
        ld = ImageDraw.Draw(loop)
        if ang < 0:
            ld.ellipse([30, 110, 205, 230], fill=blk, outline=hi, width=6)
            ld.ellipse([62, 135, 175, 205], outline=(40, 40, 48), width=8)
        else:
            ld.ellipse([195, 110, 370, 230], fill=blk, outline=hi, width=6)
            ld.ellipse([225, 135, 338, 205], outline=(40, 40, 48), width=8)
        im = Image.alpha_composite(im, loop.rotate(ang, resample=Image.BICUBIC))
    d = ImageDraw.Draw(im)
    d.polygon([(185, 190), (215, 190), (270, 385), (225, 355), (205, 392),
               (185, 355), (130, 385)], fill=blk, outline=hi)
    d.rounded_rectangle([172, 140, 228, 215], radius=14, fill=blk, outline=hi,
                        width=5)
    return im


# ---------------------------------------------------------------- helpers
def place(base, st, cx, cy, size, angle=0, shadow=True):
    s = st.resize((size, size), Image.LANCZOS)
    if angle:
        s = s.rotate(angle, expand=True, resample=Image.BICUBIC)
    x, y = int(cx - s.width / 2), int(cy - s.height / 2)
    if shadow:
        a = s.split()[3].filter(ImageFilter.GaussianBlur(9))
        sh = Image.new("RGBA", s.size, (0, 0, 0, 0))
        sh.putalpha(a.point(lambda v: int(v * 0.6)))
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(sh, (x + 8, y + 12))
        base = Image.alpha_composite(base, layer)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.paste(s, (x, y))
    return Image.alpha_composite(base, layer)


def glow(base, cx, cy, r, color, alpha, blur=60):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([cx - r, cy - r, cx + r, cy + r],
                                  fill=color + (alpha,))
    return Image.alpha_composite(base, layer.filter(ImageFilter.GaussianBlur(blur)))


def sunburst(c1, c2, cx, cy, n=30):
    im = Image.new("RGB", (SIZE, SIZE), c1)
    d = ImageDraw.Draw(im)
    R = SIZE * 2
    for i in range(1, n, 2):
        a0 = math.radians(i * 360 / n)
        a1 = math.radians((i + 1) * 360 / n)
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)),
                   (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=c2)
    return im


def vignette(img, color, strength=200):
    g = Image.radial_gradient("L").resize(img.size)
    g = g.point(lambda v: int(max(0, v - 80) * strength / 175))
    layer = Image.new("RGBA", img.size, color + (0,))
    layer.putalpha(g)
    return Image.alpha_composite(img, layer)


def sparkles(img, rnd, avoid, n, colors):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    placed = tries = 0
    while placed < n and tries < 400:
        tries += 1
        x, y = rnd.randint(40, SIZE - 40), rnd.randint(40, 600)
        if any(a <= x <= c and b <= y <= e for a, b, c, e in avoid):
            continue
        r = rnd.randint(10, 26)
        d.polygon(star_points(x, y, r, r * .22, n=4), fill=rnd.choice(colors))
        placed += 1
    return Image.alpha_composite(img, layer)


def pick_highlights(words):
    idx = [i for i, w in enumerate(words)
           if re.sub(r"[^A-Z]", "", w) in BOOST]
    cands = sorted([i for i, w in enumerate(words) if i not in idx
                    and re.sub(r"[^A-Z]", "", w) not in STOP and len(w) > 3],
                   key=lambda i: -len(words[i]))
    for i in cands:
        if len(idx) >= 2:
            break
        idx.append(i)
    return set(idx[:3])


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


def classify(text):
    low = text.lower()
    toks = set(re.findall(r"[a-z]+", low))
    if SOMBER_RE.search(low):
        mood = "somber"
    elif SPACE_RE.search(low):
        mood = "space"
    else:
        mood = "hype"
    label = "ENTERTAINMENT"
    for name, words in LABELS:
        if any(w in toks for w in words):
            label = name
            break
    hook = "JUST IN"
    for words, h in HOOKS:
        if any(w in toks for w in words):
            hook = h
            break
    face = "star"
    if toks & LOVE:
        face = "love"
    elif toks & LAUGH:
        face = "laugh"
    elif toks & SHOCK:
        face = "shock"
    if mood == "somber":
        label, hook = "TRIBUTE", "IN LOVING MEMORY"
    return mood, label, hook, face


