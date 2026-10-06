import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from card_layouts_a import *

# ------------------------------------------------------------ 5. POP ART
WORDS = {"shock": "WHOA!", "love": "AWW!", "laugh": "LOL!", "star": "WOW!"}


def bubble_shape(d, box, tail, fill, outline, w=10):
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0 + 8, y0 + 10, x1 + 8, y1 + 10], radius=80, fill=(0, 0, 0))
    d.polygon([(tail[0][0] + 8, tail[0][1] + 10), (tail[1][0] + 8, tail[1][1] + 10), (tail[2][0] + 8, tail[2][1] + 10)], fill=(0, 0, 0))
    d.rounded_rectangle(box, radius=80, fill=fill, outline=outline, width=w)
    d.polygon(tail, fill=fill, outline=outline)
    d.polygon([(tail[0][0] + 6, tail[0][1] - w + 2), (tail[1][0] - 6, tail[1][1] - w + 2), (tail[2][0], tail[2][1] - 6)], fill=fill)


def card_popart(text, ctx, rnd):
    bg = rnd.choice([(255, 214, 10), (0, 200, 240), (255, 90, 160)])
    dots = {(255, 214, 10): (255, 70, 150), (0, 200, 240): (255, 255, 255), (255, 90, 160): (255, 220, 40)}[bg]
    img = Image.new("RGB", (SIZE, SIZE), bg)
    d = ImageDraw.Draw(img)
    for gy in range(0, SIZE, 36):
        for gx in range(0, SIZE, 36):
            ox = 18 if (gy // 36) % 2 else 0
            r = max(0, 14 - (gy / SIZE) * 14)
            if r > 1.5:
                d.ellipse([gx + ox - r, gy - r, gx + ox + r, gy - r + 2 * r], fill=dots)
    d.rectangle([30, 30, SIZE - 30, SIZE - 30], outline=(0, 0, 0), width=12)
    # narration box
    nf = font_from(COND, 40)
    nw = int(d.textlength("MEANWHILE IN HOLLYWOOD...", font=nf)) + 50
    d.rectangle([62, 62, 62 + nw, 150], fill=(255, 255, 255), outline=(0, 0, 0), width=8)
    d.text((86, 86), "MEANWHILE IN HOLLYWOOD...", font=nf, fill=(0, 0, 0))
    # burst word
    cx, cy = 880, 230
    d.polygon(star_points(cx + 8, cy + 10, 170, 105, n=12, rot=-80), fill=(0, 0, 0))
    d.polygon(star_points(cx, cy, 170, 105, n=12, rot=-80), fill=(235, 30, 60), outline=(0, 0, 0))
    bw = WORDS.get(ctx["face"], "WOW!")
    txt = Image.new("RGBA", (340, 200), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt)
    td.text((170, 100), bw, font=font_from(BOLD, 74), fill=(255, 255, 255, 255), anchor="mm",
            stroke_width=6, stroke_fill=(0, 0, 0, 255))
    txt = txt.rotate(12, expand=True, resample=Image.BICUBIC)
    img.paste(txt, (cx - txt.width // 2, cy - txt.height // 2), txt)
    d = ImageDraw.Draw(img)
    # speech bubble
    box = [70, 300, 1010, 770]
    bubble_shape(d, box, [(700, 760), (820, 760), (860, 880)], (255, 255, 255), (0, 0, 0))
    words = text.split()
    hi = pick_highlights(words)
    draw_block(d, words, COND, (120, 340, 960, 740), (0, 0, 0), hi=hi,
               hi_color=(235, 30, 60), align="center", valign="middle",
               sizes=(120, 44), lh=1.08)
    # face with outline
    img = img.convert("RGBA")
    img = place(img, face_img(ctx["face"]), 860, 930, 260, 0)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    d.rectangle([62, 860, 600, 1000], fill=(0, 0, 0))
    d.rectangle([54, 852, 592, 992], fill=(255, 255, 255), outline=(0, 0, 0), width=8)
    d.text((82, 876), PAGE_NAME, font=font_from(COND, 60), fill=(235, 30, 60))
    d.text((82, 940), "FOLLOW FOR MORE!", font=font_from(COND, 40), fill=(0, 0, 0))
    return img


# ------------------------------------------------------------ 6. POSTER
def gold_text(img, xy_lines, f, anchor_w=None):
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    for (x, y, w) in xy_lines:
        md.text((x, y), w, font=f, fill=255)
    top, bot = (255, 240, 170), (190, 120, 20)
    grad = Image.new("RGB", img.size)
    gd = ImageDraw.Draw(grad)
    for y in range(SIZE):
        gd.line([(0, y), (SIZE, y)], fill=lerp(top, bot, abs((y - 520) / 380) if abs(y - 520) < 380 else 1))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    for (x, y, w) in xy_lines:
        sd.text((x + 6, y + 8), w, font=f, fill=(0, 0, 0, 220))
    img = Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(3))).convert("RGB")
    img.paste(grad, (0, 0), mask)
    return img


def card_poster(text, ctx, rnd):
    img = grad_bg((10, 6, 20), (50, 12, 40)).convert("RGBA")
    beams = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(beams)
    bd.polygon([(500, -20), (580, -20), (1000, SIZE), (80, SIZE)], fill=(255, 235, 190, 34))
    img = Image.alpha_composite(img, beams.filter(ImageFilter.GaussianBlur(10)))
    img = glow(img, SIZE // 2, 560, 330, (255, 190, 80), 80, 100)
    streak = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(streak).ellipse([60, 520, SIZE - 60, 560], fill=(255, 240, 200, 120))
    img = Image.alpha_composite(img, streak.filter(ImageFilter.GaussianBlur(14)))
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    gold = (232, 190, 90)
    d.rectangle([34, 34, SIZE - 34, SIZE - 34], outline=gold, width=6)
    d.rectangle([52, 52, SIZE - 52, SIZE - 52], outline=gold, width=2)
    d.text((SIZE // 2, 120), "A  " + PAGE_NAME + "  EXCLUSIVE", font=font_from(SERIF, 40), fill=gold, anchor="mm")
    d.polygon(star_points(SIZE // 2, 205, 30, 12), fill=gold)
    words = text.split()
    f, lines, lh = fit(d, words, SERIF, (110, 270, 970, 700), (112, 44), 4, 1.14)
    sp = d.textlength(" ", font=f)
    tot = len(lines) * lh
    y = 270 + (430 - tot) // 2
    items = []
    for line in lines:
        tw = sum(d.textlength(w, font=f) for _, w in line) + sp * (len(line) - 1)
        x = (SIZE - tw) / 2
        for i, w in line:
            items.append((x, y, w))
            x += d.textlength(w, font=f) + sp
        y += lh
    img = gold_text(img, items, f)
    d = ImageDraw.Draw(img)
    tag = {"TV NEWS": "THE SEASON EVERYONE IS TALKING ABOUT", "MOVIE NEWS": "COMING SOON TO YOUR FEED"}.get(
        ctx["label"], "THE STORY EVERYONE IS TALKING ABOUT")
    d.text((SIZE // 2, 770), tag, font=font_from(SERIF, 34), fill=(240, 225, 190), anchor="mm")
    d.rectangle([150, 810, SIZE - 150, 813], fill=gold)
    d.text((SIZE // 2, 860), "STARRING THE INTERNET  \u2022  DIRECTED BY DRAMA", font=font_from(BOLD, 28),
           fill=(200, 180, 140), anchor="mm")
    d.rounded_rectangle([60, 915, 250, 1005], radius=8, outline=(240, 225, 190), width=4)
    d.text((155, 947), "RATED", font=font_from(BOLD, 24), fill=(240, 225, 190), anchor="mm")
    d.text((155, 980), "JUICY", font=font_from(BOLD, 26), fill=(255, 210, 90), anchor="mm")
    d.text((SIZE - 60, 960), "FOLLOW " + PAGE_NAME, font=font_from(SERIF, 38), fill=gold, anchor="rm")
    return img


# ------------------------------------------------------------ 7. MAGAZINE
def card_magazine(text, ctx, rnd):
    pal = rnd.choice([((235, 40, 90), (255, 214, 10)), ((20, 120, 230), (255, 214, 10)),
                      ((120, 60, 200), (255, 214, 10)), ((235, 110, 30), (255, 255, 255))])
    bg, accent = pal
    img = Image.new("RGB", (SIZE, SIZE), bg)
    d = ImageDraw.Draw(img)
    for i in range(0, SIZE, 60):
        d.line([(i, 0), (i - 500, SIZE)], fill=lerp(bg, (255, 255, 255), 0.07), width=26)
    d.rectangle([40, 40, SIZE - 40, 330], fill=(255, 255, 255) if bg != (255, 255, 255) else (20, 20, 20))
    ms = 190
    while d.textlength(PAGE_NAME, font=font_from(SERIF, ms)) > 940:
        ms -= 4
    d.text((SIZE // 2, 185), PAGE_NAME, font=font_from(SERIF, ms), fill=bg, anchor="mm")
    d.rectangle([40, 322, SIZE - 40, 334], fill=accent)
    d.text((70, 350), ctx["label"] + "  \u2022  ISSUE 2026", font=font_from(BOLD, 30), fill=(255, 255, 255))
    img = img.convert("RGBA")
    img = glow(img, 820, 560, 260, accent, 130, 80)
    img = place(img, face_img(ctx["face"]), 800, 570, 460, 0)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    words = text.split()
    hi = pick_highlights(words)
    draw_block(d, words, BOLD, (60, 530, 560, 860), (255, 255, 255), hi=hi, hi_fill=accent,
               hi_color=bg if accent == (255, 255, 255) else (20, 20, 30),
               shadow=(0, 0, 0), valign="middle", sizes=(92, 40), lh=1.12)
    # teasers
    d.rectangle([40, 880, SIZE - 40, 884], fill=(255, 255, 255))
    d.text((60, 905), "PLUS: TODAY'S BIGGEST STORIES", font=font_from(COND, 38), fill=accent)
    d.text((60, 962), "FOLLOW " + PAGE_NAME + " FOR MORE", font=font_from(COND, 38), fill=(255, 255, 255))
    # barcode + price
    x = 790
    d.rectangle([780, 895, 1040, 1040], fill=(255, 255, 255))
    while x < 1020:
        w = rnd.choice([3, 5, 7])
        d.rectangle([x, 910, x + w, 1000], fill=(0, 0, 0))
        x += w + rnd.choice([3, 4])
    d.text((910, 1022), "ISSUE 2026 \u2022 FREE", font=font_from(BOLD, 22), fill=(0, 0, 0), anchor="mm")
    d.ellipse([60, 370, 200, 510], fill=accent, outline=(255, 255, 255), width=6)
    d.text((130, 427), "NEW", font=font_from(BOLD, 44), fill=(20, 20, 30), anchor="mm")
    d.text((130, 470), "TODAY", font=font_from(BOLD, 34), fill=(20, 20, 30), anchor="mm")
    return img
