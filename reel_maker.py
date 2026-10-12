import hashlib
import math
import os
import re
import subprocess
from PIL import Image, ImageDraw, ImageFilter
from card_layouts_a import *
import music_maker

DW, DH = 1080, 1920          # design size
OW, OH = 720, 1280           # output video size
FPS = 24
DURATION = 15.0
CRIME = re.compile(
    r"\b(police|warrant|arrest\w*|raid\w*|lawsuit|sued|charged|indict\w*|"
    r"jail|prison|court|trial|verdict|investigat\w*|cops?)\b", re.I)


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def clean_text(t):
    return "".join(c for c in t if ord(c) < 0x2600)


def split_post(post):
    lines = [l.strip() for l in post.split("\n")
             if l.strip() and not l.strip().startswith("#")
             and not l.strip().lower().startswith("source:")]
    text = clean_text(" ".join(lines))
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    question = ""
    for s in reversed(sents):
        if s.endswith("?"):
            question = s
            break
    facts = [s for s in sents if s != question and 25 <= len(s) <= 170]
    return facts[:3], question


def sunburst_big(c1, c2, n=30):
    size = 2300
    im = Image.new("RGB", (size, size), c1)
    d = ImageDraw.Draw(im)
    cx = cy = size // 2
    R = size
    for i in range(1, n, 2):
        a0 = math.radians(i * 360 / n)
        a1 = math.radians((i + 1) * 360 / n)
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)),
                   (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=c2)
    return im


def panel(text, width, height, accent, size_range):
    im = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, width, height], radius=36, fill=(10, 6, 24, 205))
    d.rounded_rectangle([0, 0, 18, height], radius=9, fill=accent)
    draw_block(d, text.split(), BOLD, (50, 18, width - 30, height - 18), (255, 255, 255),
               valign="middle", sizes=size_range, lh=1.15)
    return im


def text_layer(text, box_w, box_h, color, hi, hi_fill, hi_color, sizes, align="center"):
    im = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    draw_block(d, text.split(), COND, (0, 0, box_w, box_h), color, hi=hi, hi_fill=hi_fill,
               hi_color=hi_color, align=align, valign="middle", sizes=sizes, lh=1.12,
               shadow=(0, 0, 0) if not hi_fill else None)
    return im


def with_alpha(im, a):
    if a >= 0.999:
        return im
    out = im.copy()
    out.putalpha(im.getchannel("A").point(lambda v: int(v * max(0.0, a))))
    return out


def get_audio(text, mood, crime, out_dir):
    """Use a track from the music/ folder if there is one, else make original music."""
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % 100000
    files = []
    if os.path.isdir("music"):
        files = sorted(f for f in os.listdir("music")
                       if f.lower().endswith((".mp3", ".m4a", ".wav", ".ogg")))
    if files:
        return os.path.join("music", files[seed % len(files)])
    style = "calm" if mood == "somber" else ("news" if crime else "hype")
    path = os.path.join(out_dir, "music_%d.wav" % seed)
    music_maker.make_music(style, DURATION, path, seed)
    return path


def make_reel(headline, post, label, mood, face, hook, path):
    facts, question = split_post(post)
    title = " ".join(clean_text(headline).upper().split())[:90] or "ENTERTAINMENT NEWS"
    crime = bool(CRIME.search(title + " " + post))
    if mood == "somber":
        c1, c2, hot, pop, sticker = (10, 10, 12), (30, 26, 18), (232, 196, 110), (150, 150, 150), candle()
    elif crime:
        c1, c2, hot, pop, sticker = (8, 16, 52), (14, 40, 100), HOT, (214, 20, 40), None
    elif mood == "space":
        c1, c2, hot, pop, sticker = (8, 10, 40), (28, 14, 80), HOT, (90, 110, 255), face_img("alien")
    else:
        c1, c2, hot, pop, sticker = (92, 12, 150), (136, 26, 196), HOT, (255, 45, 120), face_img(face)
    big = sunburst_big(c1, c2)
    audio = get_audio(title, mood, crime, os.path.dirname(path) or ".")

    # static overlay: vignette + header + footer pill
    vig = Image.radial_gradient("L").resize((DW, DH)).point(lambda v: int(max(0, v - 70) * 1.5))
    vlayer = Image.new("RGBA", (DW, DH), (10, 0, 24, 0))
    vlayer.putalpha(vig)
    chrome = Image.new("RGBA", (DW, DH), (0, 0, 0, 0))
    cd = ImageDraw.Draw(chrome)
    cd.polygon(star_points(100, 118, 26, 11), fill=hot, outline=(0, 0, 0))
    cd.text((142, 88), PAGE_NAME, font=font_from(COND, 56), fill=hot, stroke_width=3, stroke_fill=(0, 0, 0))
    lf = font_from(COND, 38)
    lw = int(cd.textlength(label, font=lf)) + 60
    cd.rounded_rectangle([DW - 60 - lw, 80, DW - 60, 150], radius=35, fill=pop, outline=(255, 255, 255), width=4)
    cd.text((DW - 60 - lw + 30, 94), label, font=lf, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    pf = font_from(COND, 46)
    ptxt = "FOLLOW " + PAGE_NAME + " FOR MORE"
    pw = int(cd.textlength(ptxt, font=pf)) + 120
    pill = Image.new("RGBA", (pw, 100), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([0, 0, pw, 100], radius=50, fill=hot)
    pd.polygon(star_points(52, 50, 20, 8), fill=(20, 10, 30))
    pd.text((90, 24), ptxt, font=pf, fill=(20, 10, 30))
    sticker_big = sticker.resize((620, 620), Image.LANCZOS) if sticker else None
    glow_l = Image.new("RGBA", (DW, DH), (0, 0, 0, 0))
    ImageDraw.Draw(glow_l).ellipse([140, 330, 940, 1130], fill=hot + (90,))
    glow_l = glow_l.filter(ImageFilter.GaussianBlur(80))

    words = title.split()
    hook_layer = text_layer(title, 940, 700, (255, 255, 255), pick_highlights(words), hot,
                            (20, 10, 30), (118, 48))
    panels = [panel(f, 960, 232, hot, (50, 26)) for f in facts]
    q_layer = None
    if question:
        qw = clean_text(question).upper().split()
        q_layer = text_layer(" ".join(qw), 940, 700, (255, 255, 255), pick_highlights(qw), hot,
                             (20, 10, 30), (104, 44))
    # timeline
    n = len(panels)
    p_start = 3.8
    p_gap = 2.5 if n >= 3 else 3.0
    p_times = [p_start + i * p_gap for i in range(n)]
    panels_end = 12.0 if q_layer else DURATION + 1
    if not n:
        p_times = []
    total_frames = int(DURATION * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", "%dx%d" % (OW, OH), "-r", str(FPS), "-i", "-",
         "-stream_loop", "-1", "-i", audio,
         "-map", "0:v", "-map", "1:a", "-af", "afade=t=out:st=13.4:d=1.6",
         "-t", str(DURATION), "-c:v", "libx264", "-preset", "veryfast", "-crf", "27",
         "-maxrate", "1800k", "-bufsize", "3600k", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-movflags", "+faststart", path],
        stdin=subprocess.PIPE)
    for fi in range(total_frames):
        t = fi / FPS
        ang = t * 2.0
        rot = big.rotate(ang, resample=Image.BILINEAR)
        frame = rot.crop(((2300 - DW) // 2, (2300 - DH) // 2, (2300 + DW) // 2, (2300 + DH) // 2)).convert("RGBA")
        frame = Image.alpha_composite(frame, vlayer)
        if sticker_big:
            frame = Image.alpha_composite(frame, glow_l)
            bob = int(22 * math.sin(t * 2 * math.pi / 1.7))
            pop_s = 1.0 + 0.04 * math.sin(t * 2 * math.pi / 1.2)
            sw = int(620 * pop_s)
            sti = sticker_big.resize((sw, sw), Image.BILINEAR)
            sh = Image.new("RGBA", sti.size, (0, 0, 0, 0))
            sh.putalpha(sti.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * .55)))
            frame.alpha_composite(sh, (DW // 2 - sw // 2 + 10, 640 - sw // 2 + bob + 16))
            frame.alpha_composite(sti, (DW // 2 - sw // 2, 640 - sw // 2 + bob))
        frame = Image.alpha_composite(frame, chrome)
        # hook headline
        if t < 3.8:
            a = ease(t / 0.5) * (1 - ease((t - 3.3) / 0.5))
            y = 960 + int(40 * (1 - ease(t / 0.6)))
            frame.alpha_composite(with_alpha(hook_layer, a), (70, y))
        # fact panels
        if p_times:
            out_a = 1 - ease((t - panels_end) / 0.4) if q_layer else 1
            for i, ptm in enumerate(p_times):
                if t >= ptm and out_a > 0:
                    pa = ease((t - ptm) / 0.45) * out_a
                    py = 960 + i * 260 + int(50 * (1 - ease((t - ptm) / 0.45)))
                    frame.alpha_composite(with_alpha(panels[i], pa), (60, py))
        if q_layer and t >= 12.4:
            qa = ease((t - 12.4) / 0.5)
            frame.alpha_composite(with_alpha(q_layer, qa), (70, 960 + int(40 * (1 - qa))))
        # footer pill with gentle pulse, progress bar
        ps = 1.0 + 0.035 * math.sin(t * 2 * math.pi / 1.0)
        pw2, ph2 = int(pill.width * ps), int(pill.height * ps)
        pl = pill.resize((pw2, ph2), Image.BILINEAR)
        frame.alpha_composite(pl, ((DW - pw2) // 2, 1740 - (ph2 - 100) // 2))
        bar = ImageDraw.Draw(frame)
        bar.rectangle([0, 1900, int(DW * t / DURATION), DH], fill=hot)
        ff.stdin.write(frame.convert("RGB").resize((OW, OH), Image.LANCZOS).tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    return path
