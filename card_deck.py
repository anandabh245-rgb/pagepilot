import hashlib
import json
import random
import re

import card_maker
from card_maker import *
import card_art
from card_layouts_a import card_news, card_chat, card_neon, card_tabloid
from card_layouts_b import card_popart, card_poster, card_magazine

# Treat any sad or tragic headline as somber, so it never gets a party design.
card_maker.SOMBER_RE = re.compile(
    r"\b(passed away|dies|died|dead at|death|death of|rip|in memoriam|"
    r"remembering|we lost|we've lost|stars lost|mourn\w*|funeral|tribute|"
    r"heartbreaking|tragic|tragedy|killed|shot dead|suicide|overdose)\b")

CRIME = re.compile(
    r"\b(police|warrant|arrest\w*|raid\w*|lawsuit|sued|charged|indict\w*|"
    r"jail|prison|court|trial|verdict|investigat\w*|cops?)\b", re.I)

ORDER = ["reaction", "news", "chat", "popart", "tabloid", "neon", "poster",
         "magazine"]
FUNCS = {"news": card_news, "chat": card_chat, "popart": card_popart,
         "tabloid": card_tabloid, "neon": card_neon, "poster": card_poster,
         "magazine": card_magazine}


def pick_layout(label):
    try:
        with open("data/posted.json", encoding="utf-8") as f:
            n = len(json.load(f))
    except Exception:
        n = 0
    name = ORDER[n % len(ORDER)]
    if name == "poster" and label not in ("TV NEWS", "MOVIE NEWS"):
        name = "neon"
    return name


def make_card(headline, path, force=None):
    text = "".join(c for c in headline if ord(c) < 0x2600)
    text = " ".join(text.upper().split())[:90] or "ENTERTAINMENT NEWS"
    mood, label, hook, face = classify(text)
    name = force or pick_layout(label)
    if not force and CRIME.search(text):
      name = "neon"
    if mood in ("somber", "space") or name == "reaction":
        return card_art.make_card(headline, path)
    rnd = random.Random(int(hashlib.md5(text.encode()).hexdigest(), 16))
    ctx = {"mood": mood, "label": label, "hook": hook, "face": face}
    img = FUNCS[name](text, ctx, rnd)
    img.save(path, "PNG")
    return path
