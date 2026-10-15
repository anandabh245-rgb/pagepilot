import email.utils
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, urlunparse

# (source name, feed url, trusted niche feed: every item is on-topic)
FEEDS = [
    ("ComicBook.com", "https://comicbook.com/category/marvel/feed/", True),
    ("ComicBook.com", "https://comicbook.com/category/starwars/feed/", True),
    ("ComicBook.com", "https://comicbook.com/feed/", False),
    ("ComicBook.com", "https://comicbook.com/category/dc/feed/", False),
    ("Screen Rant", "https://screenrant.com/feed/comics/", False),
    ("Screen Rant", "https://screenrant.com/feed/", False),
    ("The Hollywood Reporter", "https://www.hollywoodreporter.com/feed/", False),
    ("Variety", "https://variety.com/feed/", False),
    ("Deadline", "https://deadline.com/feed/", False),
    ("/Film", "https://feeds.feedburner.com/slashfilm", False),
]
NEWS_ONLY = {"ComicBook.com"}      # only links with /news/ (skips opinion and lists)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
MAX_AGE_HOURS = 72
PER_SOURCE = 6
POOL = 16

NICHE = re.compile(
    r"\b(marvel|mcu|avengers|spider-?man|x-men|deadpool|wolverine|iron man|"
    r"captain america|black panther|guardians of the galaxy|fantastic four|"
    r"doctor strange|thor|hulk|daredevil|loki|wanda|vision|"
    r"star wars|mandalorian|jedi|andor|skywalker|lucasfilm|grogu|darth|ahsoka|"
    r"sith|stormtrooper|obi-wan|"
    r"superman|batman|joker|justice league|wonder woman|aquaman|dc studios|"
    r"dcu|green lantern|supergirl|flash|superhero|superheroes|the boys|"
    r"invincible|peacemaker|james gunn|kevin feige)\b", re.I)

SKIP = re.compile(
    r"\b(prime day|big deal days|deals?|on sale|discount\w*|coupon\w*|promo code|"
    r"gift guide|where to buy|shopping|horoscope|quiz|crossword|wordle|"
    r"masturbat\w*|nude|naked|porn\w*|sex tape|onlyfans|nipple\w*|"
    r"trump|biden|harris|election\w*|congress|senate|gaza|israel\w*|palestin\w*|"
    r"ukraine|republican\w*|democrat\w*)\b", re.I)
BAD_URL = re.compile(r"(product-recommendations|/shopping/|/deals?/|gift-guide|/politics/)", re.I)
RISKY = re.compile(
    r"\b(rape\w*|sexual(ly)? (assault\w*|abus\w*|misconduct)|molest\w*|"
    r"trafficking|child abuse|pedophil\w*)\b", re.I)
GENERIC = {"marvel", "star", "wars", "fans", "studios", "movie", "film", "series",
           "show", "season", "about", "after", "their", "this", "that", "with",
           "from", "what", "will", "just", "into", "here", "first", "every",
           "best", "most", "could", "would", "official", "finally", "confirms",
           "reveals", "revealed", "new", "marvel's", "superhero", "dcu"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")


def strip_html(text):
    text = re.sub(r"(?s)<[^>]+>", " ", text or "")
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
            .replace("&#8217;", "'").replace("&#8220;", '"')
            .replace("&#8221;", '"'))
    return re.sub(r"\s+", " ", text).strip()


def clean_link(link):
    p = urlparse(link.strip())
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def posted_keys():
    try:
        with open("data/posted.json", encoding="utf-8") as f:
            return {e.get("key") for e in json.load(f) if isinstance(e, dict)}
    except Exception:
        return set()


def tokens(title):
    return {w for w in re.findall(r"[a-z0-9']+", title.lower())
            if len(w) > 3 and w not in GENERIC}


def similar(a, b):
    inter = len(a & b)
    return inter >= 2 or (a and b and inter / min(len(a), len(b)) >= 0.5)


def read_feed(name, url, trusted):
    out = []
    try:
        root = ET.fromstring(get(url))
    except Exception as e:
        print("feed error", name, url, str(e)[:60])
        return out
    now = datetime.now(timezone.utc)
    for it in root.iter("item"):
        title = strip_html(it.findtext("title"))
        link = clean_link(it.findtext("link") or "")
        if not title or not link:
            continue
        desc = strip_html(it.findtext("description"))
        try:
            when = email.utils.parsedate_to_datetime(it.findtext("pubDate") or "")
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
        except Exception:
            when = now
        if now - when > timedelta(hours=MAX_AGE_HOURS):
            continue
        if name in NEWS_ONLY and "/news/" not in link:
            continue
        if not trusted and not NICHE.search(title + " " + desc):
            continue
        if (SKIP.search(title) or RISKY.search(title) or BAD_URL.search(link)
                or re.search(r"\d+% off|shop here", title, re.I)):
            continue
        out.append({"title": title, "link": link, "source": name,
                    "description": desc, "published": when.isoformat()})
    return out


def main():
    posted = posted_keys()
    per_feed, seen_links = [], set()
    for name, url, trusted in FEEDS:
        items = []
        for s in read_feed(name, url, trusted):
            if s["link"] in posted or s["link"] in seen_links:
                continue
            seen_links.add(s["link"])
            items.append(s)
        print(name, "| usable stories:", len(items))
        per_feed.append(items[:PER_SOURCE])
    merged, chosen_tokens = [], []
    for i in range(PER_SOURCE):
        for items in per_feed:
            if i < len(items):
                s = items[i]
                tk = tokens(s["title"])
                if any(similar(tk, other) for other in chosen_tokens):
                    continue
                chosen_tokens.append(tk)
                merged.append(s)
    stories = merged[:POOL]
    with open("data/stories.json", "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(),
                   "story_count": len(stories), "stories": stories},
                  f, indent=2, ensure_ascii=False)
    print("Saved", len(stories), "stories")
    if not stories:
        raise SystemExit("No stories found")


if __name__ == "__main__":
    main()
