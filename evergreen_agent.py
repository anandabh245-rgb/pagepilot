"""
evergreen_agent.py - evergreen and Avengers: Doomsday Reel posts.

Facts come from Wikipedia text (not from the AI's memory). Gemini writes a short
post from that text, and the same fact-checker used for your news posts must pass it.
Finished posts wait in data/evergreen_posts.json until a Reel uses them.
"""
import json
import os
import random
import re
import sys
import urllib.parse
import urllib.request

import story_agent as sa   # reuses the Gemini helper, fact-check and safety filters

OUT = "data/evergreen_posts.json"
LOG = "data/reels_posted.json"
WANT_READY = {"doomsday": 5, "evergreen": 8}      # unused posts to keep in the queue
MAX_BUILDS = int(os.environ.get("MAX_BUILDS", "6"))  # Gemini attempts per run
WIKI_UA = {"User-Agent": "PagePilotBot/1.0 (https://github.com/anandabh245-rgb/pagepilot)"}
DROP = {"plot", "synopsis", "references", "external links", "notes", "see also",
        "further reading", "bibliography", "footnotes", "sources", "citations"}

DOOM_PAGE = "Avengers: Doomsday"
DOOM_SOLO_ANGLES = [
    "what has been officially confirmed about the cast",
    "the production and filming facts",
    "the release date and how the release plans changed",
    "who is directing and writing it and why that matters",
    "how earlier Marvel films set this movie up",
]
DOOM_COMPANIONS = [
    ("Avengers: Endgame", ["Avengers Endgame", "Russo brothers"]),
    ("Avengers: Infinity War", ["Avengers Infinity War", "Russo brothers"]),
    ("Avengers: Age of Ultron", ["Avengers Age of Ultron"]),
    ("The Avengers (2012 film)", ["The Avengers", "Joss Whedon"]),
    ("Captain America: Civil War", ["Captain America Civil War"]),
    ("Doctor Doom", ["Doctor Doom"]),
    ("The Fantastic Four: First Steps", ["Fantastic Four"]),
    ("Thunderbolts*", ["Thunderbolts"]),
    ("X-Men (film series)", ["X-Men"]),
]

EVERGREEN_ANGLES = [
    "an interesting behind-the-scenes production fact",
    "a casting story: who else was considered or how the cast got their roles",
    "a box office, record or release fact",
    "how the film shaped later superhero or sci-fi movies",
]
# (Wikipedia page title, photo search hints)
EVERGREEN_PAGES = [
    ("Iron Man (2008 film)", ["Iron Man", "Robert Downey Jr"]),
    ("The Incredible Hulk (film)", ["Incredible Hulk"]),
    ("Thor (film)", ["Chris Hemsworth"]),
    ("Captain America: The First Avenger", ["Chris Evans"]),
    ("The Avengers (2012 film)", ["The Avengers"]),
    ("Guardians of the Galaxy (film)", ["Guardians of the Galaxy", "James Gunn"]),
    ("Black Panther (film)", ["Black Panther"]),
    ("Avengers: Infinity War", ["Avengers Infinity War"]),
    ("Avengers: Endgame", ["Avengers Endgame"]),
    ("Spider-Man: No Way Home", ["Spider-Man No Way Home", "Tom Holland"]),
    ("Spider-Man (2002 film)", ["Spider-Man", "Tobey Maguire"]),
    ("Deadpool & Wolverine", ["Hugh Jackman", "Ryan Reynolds"]),
    ("Deadpool (film)", ["Ryan Reynolds"]),
    ("Logan (film)", ["Hugh Jackman"]),
    ("X-Men (film)", ["X-Men", "Hugh Jackman"]),
    ("Doctor Strange (2016 film)", ["Benedict Cumberbatch"]),
    ("Thor: Ragnarok", ["Taika Waititi", "Chris Hemsworth"]),
    ("Captain Marvel (film)", ["Brie Larson"]),
    ("Black Widow (2021 film)", ["Scarlett Johansson"]),
    ("Fantastic Four (2005 film)", ["Fantastic Four"]),
    ("Blade (1998 film)", ["Wesley Snipes"]),
    ("The Dark Knight", ["Christopher Nolan", "Christian Bale"]),
    ("Batman Begins", ["Christopher Nolan", "Christian Bale"]),
    ("Batman (1989 film)", ["Tim Burton", "Michael Keaton"]),
    ("Man of Steel (film)", ["Henry Cavill"]),
    ("Superman (1978 film)", ["Christopher Reeve"]),
    ("Wonder Woman (2017 film)", ["Gal Gadot"]),
    ("Joker (2019 film)", ["Joaquin Phoenix"]),
    ("Star Wars (film)", ["Star Wars", "George Lucas"]),
    ("The Empire Strikes Back", ["Star Wars", "Harrison Ford"]),
    ("Return of the Jedi", ["Star Wars", "Mark Hamill"]),
    ("Star Wars: The Force Awakens", ["Star Wars", "Daisy Ridley"]),
    ("Rogue One", ["Star Wars", "Felicity Jones"]),
    ("The Mandalorian", ["Pedro Pascal", "Star Wars"]),
    ("Andor (TV series)", ["Diego Luna", "Star Wars"]),
    ("Loki (TV series)", ["Tom Hiddleston"]),
]


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def prune(text):
    """Drop plot/reference style sections, keep production, cast and release facts."""
    parts = re.split(r"\n\s*(={2,})\s*([^=\n]+?)\s*={2,}\s*\n", text)
    out = [parts[0]]
    skip_level = None
    for i in range(1, len(parts) - 2, 3):
        level, name, body = len(parts[i]), parts[i + 1].strip().lower(), parts[i + 2]
        if skip_level is not None and level > skip_level:
            continue
        skip_level = None
        if name in DROP:
            skip_level = level
            continue
        out.append(body)
    return " ".join(" ".join(out).split())


_CACHE = {}


def wiki(title):
    """Return (clean text, page title) or ("", "") if the page can't be read."""
    if title in _CACHE:
        return _CACHE[title]
    q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1,
                                "redirects": 1, "format": "json", "titles": title})
    res = ("", "")
    try:
        req = urllib.request.Request("https://en.wikipedia.org/w/api.php?" + q, headers=WIKI_UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        page = next(iter(data.get("query", {}).get("pages", {}).values()), {})
        if "missing" not in page and page.get("extract"):
            res = (prune(page["extract"]), page.get("title", title))
    except Exception as e:
        print("Wikipedia error for", title, ":", str(e)[:80])
    _CACHE[title] = res
    return res


def cap(text, n):
    return " ".join(text.split()[:n])


def candidates():
    doom, ever = [], []
    for angle in DOOM_SOLO_ANGLES:
        doom.append({"key": "doomsday:solo:" + slug(angle), "type": "doomsday",
                     "pages": [DOOM_PAGE], "hints": ["Avengers Doomsday", "Russo brothers"],
                     "focus": "Avengers: Doomsday - " + angle})
    for title, hints in DOOM_COMPANIONS:
        doom.append({"key": "doomsday:" + slug(title), "type": "doomsday",
                     "pages": [DOOM_PAGE, title], "hints": hints,
                     "focus": ("how " + title + " connects to Avengers: Doomsday. Only use "
                               "connections that are stated in the texts")})
    for title, hints in EVERGREEN_PAGES:
        for angle in EVERGREEN_ANGLES:
            ever.append({"key": "evergreen:" + slug(title) + ":" + slug(angle),
                         "type": "evergreen", "pages": [title], "hints": hints,
                         "focus": angle})
    return doom, ever


def make_post(c):
    texts, names = [], []
    per_page = 1700 if len(c["pages"]) == 1 else 900
    for t in c["pages"]:
        text, real = wiki(t)
        if not text:
            return None
        texts.append((real, cap(text, per_page)))
        names.append(real)
    if sa.RISKY.search(" ".join(t for _, t in texts)):
        return None
    if len(texts) == 1:
        body = texts[0][1]
    else:
        body = "\n\n".join("SOURCE %d (%s):\n%s" % (i + 1, n, t)
                           for i, (n, t) in enumerate(texts))
    title = ("Throwback fan trivia about " + names[-1] + ": " + c["focus"] +
             ". Pick ONE specific fact from the text. Do not present it as breaking news.")
    story = {"title": title, "text": body, "source": "Wikipedia",
             "link": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(names[-1].replace(" ", "_"))}
    p = sa.build(story, "card")
    if not p:
        return None
    if sa.SENSITIVE.search(p["post"]) or sa.RISKY.search(p["post"]):
        print("  skipped: sensitive wording")
        return None
    p.update({"key": c["key"], "type": c["type"], "photo_queries": c["hints"], "kind": "card"})
    return p


def main():
    if not sa.API_KEY:
        print("GEMINI_API_KEY is missing")
        return 1
    log_keys = {e.get("key") for e in load(LOG, []) if isinstance(e, dict)}
    queue = [p for p in load(OUT, []) if isinstance(p, dict) and p.get("key") not in log_keys]
    used = log_keys | {p.get("key") for p in queue}
    doom, ever = candidates()
    builds = 0
    for typ, cands in (("doomsday", doom), ("evergreen", ever)):
        random.shuffle(cands)
        ready = sum(1 for p in queue if p.get("type") == typ)
        for c in cands:
            if ready >= WANT_READY[typ] or builds >= MAX_BUILDS:
                break
            if c["key"] in used:
                continue
            used.add(c["key"])
            builds += 1
            print("Building", typ, "|", c["focus"][:70])
            p = make_post(c)
            if p:
                queue.append(p)
                ready += 1
                print("  READY:", p["headline"])
    os.makedirs("data", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
    print("Queue now has", sum(p.get("type") == "doomsday" for p in queue), "Doomsday and",
          sum(p.get("type") == "evergreen" for p in queue), "evergreen posts")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)
                                     
