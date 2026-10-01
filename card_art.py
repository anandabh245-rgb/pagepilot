import hashlib
import random
from PIL import Image, ImageDraw, ImageFilter
from card_maker import *

# ---------------------------------------------------------------- scenes
def scene_hype(rnd, face):
    img = sunburst((92, 12, 150), (136, 26, 196), SIZE // 2, 390).convert("RGBA")
    img = vignette(img, (14, 0, 30))
    img = glow(img, SIZE // 2, 390, 260, (255, 214, 10), 150, 70)
    img = glow(img, 130, 300, 140, (255, 45, 120), 110, 60)
    img = glow(img, 950, 320, 150, (80, 200, 255), 90, 60)
    img = sparkles(img, rnd, [(300, 180, 780, 590), (50, 40, 1040, 140), (30, 440, 520, 600)], 12,
                   [(255, 255, 255, 235), HOT + (235,)])
    pool = [popcorn, clapper, flash, trophy, mic, heart_st, star_st]
    rnd.shuffle(pool)
    slots = [(135, 245, 150, -12), (295, 188, 100, 10), (105, 410, 112, 8),
             (945, 215, 135, 12), (915, 435, 140, -10), (790, 190, 96, -8)]
    for fn, (x, y, s, a) in zip(pool, slots):
        img = place(img, fn(), x, y, s, a)
    for (x, y, s, a, k) in [(272, 335, 82, -10, rnd.choice(["star", "love", "laugh"])),
                            (985, 330, 82, 10, rnd.choice(["shock", "star", "laugh"]))]:
        img = place(img, face_img(k), x, y, s, a)
    img = place(img, face_img(face), SIZE // 2, 385, 400, 0)
    return img, (255, 45, 120), HOT, DARK


def scene_space(rnd, face):
    top, bot = (6, 8, 34), (28, 10, 70)
    img = Image.new("RGB", (SIZE, SIZE), top)
    d = ImageDraw.Draw(img)
    for y in range(SIZE):
        d.line([(0, y), (SIZE, y)], fill=lerp(top, bot, y / SIZE))
    img = img.convert("RGBA")
    img = glow(img, 200, 250, 230, (110, 60, 220), 150, 80)
    img = glow(img, 900, 420, 230, (30, 170, 200), 120, 80)
    img = glow(img, SIZE // 2, 390, 240, (255, 214, 10), 70, 80)
    st = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    for _ in range(170):
        x, y, r = rnd.randint(0, SIZE), rnd.randint(0, 640), rnd.choice([1, 1, 2, 3])
        sd.ellipse([x - r, y - r, x + r, y + r],
                   fill=(255, 255, 255, rnd.randint(110, 255)))
    img = Image.alpha_composite(img, st)
    img = sparkles(img, rnd, [(300, 180, 780, 590), (50, 40, 1040, 140), (30, 440, 520, 600)], 10,
                   [(255, 255, 255, 240), HOT + (240,)])
    img = place(img, planet((70, 40, 140), (200, 140, 255)), 140, 262, 190, 0)
    img = place(img, moon(), 300, 175, 100, 15)
    img = place(img, rocket(), 945, 235, 160, 38)
    img = place(img, planet((10, 90, 110), (110, 230, 230), ring=False), 915, 455, 120, 0)
    img = place(img, star_st(), 790, 195, 70, 10)
    img = place(img, face_img("alien"), SIZE // 2, 385, 400, 0)
    helmet = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(helmet)
    hd.ellipse([SIZE // 2 - 214, 171, SIZE // 2 + 214, 599],
               fill=(190, 225, 255, 38), outline=(225, 242, 255, 210), width=9)
    hd.arc([SIZE // 2 - 170, 215, SIZE // 2 + 170, 555], 200, 255,
           fill=(255, 255, 255, 230), width=14)
    img = Image.alpha_composite(img, helmet)
    return img, (90, 110, 255), HOT, (6, 8, 34)


def scene_somber(rnd):
    img = sunburst((10, 10, 12), (26, 22, 16), SIZE // 2, 330, n=36).convert("RGBA")
    img = vignette(img, (0, 0, 0), 230)
    img = glow(img, SIZE // 2, 250, 230, (255, 170, 60), 120, 90)
    img = glow(img, SIZE // 2, 330, 330, (232, 196, 110), 55, 100)
    img = place(img, lily(), 215, 440, 250, -22)
    img = place(img, lily(), 865, 440, 250, 22)
    img = place(img, bow(), 915, 205, 190, 12)
    img = place(img, candle(), SIZE // 2, 345, 340, 0)
    return img, (150, 150, 150), (232, 196, 110), (14, 12, 10)


# ---------------------------------------------------------------- card
def make_card(headline, path):
    text = "".join(c for c in headline if ord(c) < 0x2600)
    text = " ".join(text.upper().split())[:90] or "ENTERTAINMENT NEWS"
    mood, label, hook, face = classify(text)
    rnd = random.Random(int(hashlib.md5(text.encode()).hexdigest(), 16))

    if mood == "somber":
        img, pop, hot, dark = scene_somber(rnd)
    elif mood == "space":
        img, pop, hot, dark = scene_space(rnd, face)
    else:
        img, pop, hot, dark = scene_hype(rnd, face)

    band = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    for y in range(540, SIZE):
        t = min(1.0, (y - 540) / 120)
        bd.line([(0, y), (SIZE, y)], fill=(8, 4, 16, int(238 * t)))
    img = Image.alpha_composite(img, band).convert("RGB")
    d = ImageDraw.Draw(img)

    d.polygon(star_points(100, 92, 24, 10), fill=hot, outline=(0, 0, 0))
    d.text((138, 66), PAGE_NAME, font=font(46), fill=hot, stroke_width=3,
           stroke_fill=(0, 0, 0))
    cf = font(30)
    cw = int(d.textlength(label, font=cf)) + 54
    x1 = SIZE - 64
    d.rounded_rectangle([x1 - cw, 58, x1, 122], radius=32, fill=pop,
                        outline=(255, 255, 255), width=4)
    d.text((x1 - cw + 27, 74), label, font=cf, fill=(255, 255, 255),
           stroke_width=2, stroke_fill=(0, 0, 0))

    hf = font(46)
    hw = int(d.textlength(hook, font=hf)) + 60
    st = Image.new("RGBA", (hw + 40, 130), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([20, 22, hw + 20, 96], radius=16, fill=(0, 0, 0, 160))
    sd.rounded_rectangle([14, 14, hw + 14, 88], radius=16,
                         fill=hot if mood == "somber" else pop,
                         outline=(255, 255, 255), width=5)
    sd.text((14 + 30, 24), hook, font=hf,
            fill=dark if mood == "somber" else (255, 255, 255),
            stroke_width=2,
            stroke_fill=(255, 255, 255) if mood == "somber" else (0, 0, 0))
    st = st.rotate(6, expand=True, resample=Image.BICUBIC)
    img.paste(st, (40, 470), st)
    d = ImageDraw.Draw(img)

    words = text.split()
    hi = pick_highlights(words)
    max_w, max_h = 900, 330
    for size in range(116, 51, -4):
        fnt = font(size)
        lines = layout(d, words, fnt, max_w)
        line_h = int(size * 1.17)
        if len(lines) * line_h <= max_h:
            break
    space = d.textlength(" ", font=fnt)
    y = 612 + (max_h - len(lines) * line_h) // 2
    for line in lines:
        total = sum(d.textlength(w, font=fnt) for _, w in line) + space * (len(line) - 1)
        x = (SIZE - total) / 2
        for i, w in line:
            ww = d.textlength(w, font=fnt)
            if i in hi:
                bb = d.textbbox((x, y), w, font=fnt)
                d.rounded_rectangle([bb[0] - 12, bb[1] - 8, bb[2] + 12, bb[3] + 8],
                                    radius=14, fill=hot)
                d.text((x, y), w, font=fnt, fill=dark)
            else:
                d.text((x + 5, y + 6), w, font=fnt, fill=(0, 0, 0))
                d.text((x, y), w, font=fnt, fill=(255, 255, 255),
                       stroke_width=2, stroke_fill=(0, 0, 0))
            x += ww + space
        y += line_h

    ff = font(30)
    txt = "FOLLOW " + PAGE_NAME + " FOR MORE"
    fw = int(d.textlength(txt, font=ff)) + 96
    fx = (SIZE - fw) // 2
    d.rounded_rectangle([fx, 975, fx + fw, 1042], radius=34, fill=hot)
    d.polygon(star_points(fx + 40, 1008, 16, 7), fill=dark)
    d.text((fx + 70, 990), txt, font=ff, fill=dark)

    img.save(path, "PNG")
    return path
