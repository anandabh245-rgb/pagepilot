import html as htmllib
import json
import os
import re
import time
import urllib.error
import urllib.request

STORIES = "data/stories.json"
OUT = "data/final_posts.json"
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash-lite"
API_URL = os.environ.get("GEMINI_API_URL") or (
    "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL
    + ":generateContent")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
WANT_CARDS = 5
WANT_STORIES = 2
SENSITIVE = re.compile(
    r"\b(dies|died|death|dead|funeral|suicide|overdose|killed|murder\w*|"
    r"shooting|cancer|tragic|tragedy|passed away|abuse|assault|police|"
    r"warrant|arrest\w*|raid\w*|lawsuit|sued|charged|indict\w*|jail|prison)\b",
    re.I)
RISKY = re.compile(
    r"\b(cornell 7|rape\w*|sexual(ly)? (assault\w*|abus\w*|misconduct)|molest\w*|"
    r"trafficking|child abuse|pedophil\w*)\b", re.I)
PROMO = re.compile(
    r"(prime day|big deal days|promo code|% off|affiliate)", re.I)
USED = set()
BOILER = re.compile(
    r"(sign up|subscribe|newsletter|advertisement|all rights reserved|\u00a9|"
    r"click here|follow us|read more|read on|related:|privacy policy|"
    r"terms of use)", re.I)

FACTS = (
    "FACTS: Use ONLY facts stated in the SOURCE TEXT. Never invent quotes, "
    "numbers, dates, names, reactions or backstory. For allegations, lawsuits, "
    "arrests or rumors say \"alleged\", \"reportedly\" or \"according to\", and "
    "never state guilt as fact. Do not copy sentences from the source.\n")
HEADLINE = (
    "HEADLINE: a punchy 4 to 8 word line for a graphic card. It must name the "
    "main person, show or movie and tease the news, for example \"Costner and "
    "Grimes: the silence\" or \"Apple brings Dolby Atmos to F1\" (never reuse "
    "these exact words). It must be truthful: do not claim what fans or "
    "people think, feel or are doing unless the source says so, and never "
    "start with \"Fans are\" or \"Wait until\".\n")
JSON_RULE = ("Return ONLY JSON with exactly these fields: "
             "{\"headline\": \"...\", \"post\": \"...\"}\n")
CARD_RULES = (
    "You edit a popular US entertainment Facebook Page. Write ONE short "
    "original Facebook post about the story below.\n" + FACTS +
    "STYLE: 50 to 90 words in 2 or 3 short paragraphs, warm and "
    "conversational, plain language, at most 2 emojis. End with ONE easy "
    "question that invites opinions. The final line is exactly 3 relevant "
    "hashtags.\n" + HEADLINE + JSON_RULE)
STORY_RULES = (
    "You edit a popular US entertainment Facebook Page. Write a short "
    "ORIGINAL news story for Facebook about the story below.\n" + FACTS +
    "STYLE: 150 to 200 words in 3 or 4 short paragraphs. Warm and human, like "
    "a friend explaining the news. Vary sentence length. Open with the most "
    "interesting fact. No clickbait and no filler. At most 2 emojis. Credit "
    "the publication once, for example \"according to Variety\". Any words "
    "taken from the source must be under 10 words, in quotation marks and "
    "attributed. End with ONE easy question. The final line is exactly 3 "
    "relevant hashtags.\n" + HEADLINE + JSON_RULE)
SENSITIVE_NOTE = (
    "This story involves a death, crime or tragedy. Use a respectful, gentle "
    "tone, no emojis, no jokes, and do not ask readers about their own loss "
    "or pain. Do not ask a question. End with one short, neutral line, for "
    "example saying updates will follow.\n")
CHECK = (
    "You are a strict fact-checker. Compare the DRAFT to the SOURCE TEXT. "
    "List every factual claim in the DRAFT (names, numbers, dates, events, "
    "quotes, causes) that the SOURCE TEXT does not clearly support or that "
    "changes its meaning. The first line of the DRAFT is a card headline: it "
    "must not claim fan reactions or facts the source does not support. "
    "Ignore tone, hashtags, emojis and the closing "
    "question. Return ONLY JSON: {\"ok\": true or false, \"problems\": "
    "[\"...\"]}. Use ok=true only if there are no problems.")


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")


def clean(text):
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text or "")
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", htmllib.unescape(text)).strip()


def find_body(obj):
    if isinstance(obj, dict):
        if isinstance(obj.get("articleBody"), str):
            return obj["articleBody"]
        for v in obj.values():
            r = find_body(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_body(v)
            if r:
                return r
    return ""


def article_text(page):
    for m in re.finditer(
            r"(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>", page):
        try:
            body = find_body(json.loads(m.group(1)))
        except Exception:
            continue
        if body and len(body.split()) > 120:
            return clean(body)
    m = re.search(r"(?is)<article.*?</article>", page)
    scope = m.group(0) if m else page
    paras = [clean(p) for p in re.findall(r"(?is)<p[^>]*>(.*?)</p>", scope)]
    return " ".join(p for p in paras
                    if len(p.split()) >= 8 and not BOILER.search(p))


def ask(prompt):
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json",
                             "temperature": 0.7}}).encode("utf-8")
    for attempt in range(5):
        time.sleep(float(os.environ.get("GEMINI_PAUSE", "3")))
        req = urllib.request.Request(
            API_URL, data=body, method="POST",
            headers={"Content-Type": "application/json",
                     "x-goog-api-key": API_KEY or ""})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                res = json.loads(r.read().decode("utf-8"))
            data = json.loads(
                res["candidates"][0]["content"]["parts"][0]["text"].strip())
            return data[0] if isinstance(data, list) and data else data
        except urllib.error.HTTPError as e:
            if e.code in (408, 429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(8 * 2 ** attempt)
                continue
            print("Gemini HTTP error", e.code)
            return None
        except (urllib.error.URLError, KeyError, IndexError, ValueError) as e:
            if attempt < 4:
                time.sleep(4 * (attempt + 1))
                continue
            print("Gemini failed:", e)
            return None
    return None


def build(story, kind):
    text = story["text"]
    sensitive = bool(SENSITIVE.search(story["title"] + " " + text[:600]))
    rules = STORY_RULES if kind == "story" else CARD_RULES
    base = (rules + (SENSITIVE_NOTE if sensitive else "") +
            "\nPUBLICATION: " + story["source"] + "\nTITLE: " + story["title"] +
            "\nSOURCE TEXT:\n" + text + "\n")
    lo, hi = (650, 1700) if kind == "story" else (150, 900)
    notes = ""
    for _ in range(2):
        d = ask(base + notes)
        if not isinstance(d, dict) or not d.get("post") or not d.get("headline"):
            continue
        post = str(d["post"]).strip()
        if not lo <= len(post) <= hi:
            notes = "\nYOUR LAST DRAFT HAD THE WRONG LENGTH. Follow the word count exactly.\n"
            continue
        if post.count("#") < 3:
            post += "\n\n#Entertainment #Hollywood #PopCulture"
        if str(d["headline"]).strip().lower() in USED:
            notes = "\nTHAT HEADLINE WAS ALREADY USED TODAY. Write a different one.\n"
            continue
        chk = ask(CHECK + "\n\nSOURCE TEXT:\n" + text + "\n\nDRAFT:\n"
                  + str(d["headline"]) + "\n" + post)
        if isinstance(chk, dict) and chk.get("ok") is True:
            USED.add(str(d["headline"]).strip().lower())
            return {"headline": str(d["headline"]).strip(), "post": post,
                    "source": story["source"], "source_url": story["link"],
                    "original_title": story["title"], "kind": kind}
        problems = chk.get("problems", []) if isinstance(chk, dict) else []
        print("  fact-check failed:", "; ".join(map(str, problems))[:160])
        notes = ("\nA FACT-CHECK FOUND THESE PROBLEMS. Remove or correct them: "
                 + "; ".join(map(str, problems))[:600] + "\n")
    return None


def main():
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY secret is missing")
    with open(STORIES, encoding="utf-8") as f:
        stories = json.load(f)["stories"]
    for s in stories:
        text = ""
        try:
            text = article_text(fetch(s["link"]))
        except Exception as e:
            print("page error:", s["source"], str(e)[:60])
        s["thin"] = len(text.split()) < 120
        if s["thin"]:
            text = s.get("description", "")
        s["text"] = " ".join(text.split()[:1800])
        s["words"] = len(s["text"].split())
        print(s["source"], "|", s["words"], "words |", s["title"][:60])
    usable = [s for s in stories if s["words"] >= 25
              and not RISKY.search(s["title"] + " " + s["text"])
              and not PROMO.search(s["text"][:3000])]

    story_pool = sorted(
        [s for s in usable if not s["thin"] and s["words"] >= 300
         and not SENSITIVE.search(s["title"])],
        key=lambda s: -s["words"])
    long_posts, used = [], set()
    for s in story_pool[:5]:
        if len(long_posts) >= WANT_STORIES:
            break
        p = build(s, "story")
        if p:
            used.add(s["link"])
            long_posts.append(p)
            print("STORY ready:", p["headline"])
    cards = []
    for s in usable:
        if len(cards) >= WANT_CARDS:
            break
        if s["link"] in used:
            continue
        p = build(s, "card")
        if p:
            cards.append(p)
            print("CARD ready:", p["headline"])

    order, c, l = [], list(cards), list(long_posts)
    for slot in ["c", "c", "s", "c", "c", "s", "c"]:
        src = c if slot == "c" else l
        if src:
            order.append(src.pop(0))
    order += c + l
    if not order:
        raise SystemExit("No posts passed the fact-check")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(order, f, indent=2, ensure_ascii=False)
    print("Saved", len(order), "posts:", sum(p["kind"] == "story" for p in order),
          "stories")


if __name__ == "__main__":
    main()
