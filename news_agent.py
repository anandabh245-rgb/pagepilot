import email.utils
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, urlunparse

FEEDS = [
    ("Variety", "https://variety.com/feed/"),
    ("The Hollywood Reporter", "https://www.hollywoodreporter.com/feed/"),
    ("Deadline", "https://deadline.com/feed/"),
    ("E! News", "https://www.eonline.com/syndication/feeds/rssfeeds/topstories.xml"),
    ("Rolling Stone", "https://www.rollingstone.com/feed/"),
    ("Page Six", "https://pagesix.com/feed/"),
    ("TMZ", "https://www.tmz.com/rss.xml"),
]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
MAX_AGE_HOURS = 72
PER_SOURCE = 5
POOL = 16

# Shopping, quizzes, explicit content and politics are skipped.
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


def read_feed(name, url):
    out = []
    try:
        root = ET.fromstring(get(url))
    except Exception as e:
        print("feed error", name, e)
        return out
    now = datetime.now(timezone.utc)
    for it in root.iter("item"):
        title = strip_html(it.findtext("title"))
        link = clean_link(it.findtext("link") or "")
        if not title or not link:
            continue
        try:
            when = email.utils.parsedate_to_datetime(it.findtext("pubDate") or "")
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
        except Exception:
            when = now
        if now - when > timedelta(hours=MAX_AGE_HOURS):
            continue
        if (SKIP.search(title) or RISKY.search(title) or BAD_URL.search(link)
                or re.search(r"\d+% off|shop here", title, re.I)):
            continue
        out.append({"title": title, "link": link, "source": name,
                    "description": strip_html(it.findtext("description")),
                    "published": when.isoformat()})
    return out


def main():
    posted = posted_keys()
    per_feed = []
    for name, url in FEEDS:
        items = [s for s in read_feed(name, url) if s["link"] not in posted]
        print(name, "usable stories:", len(items))
        per_feed.append(items[:PER_SOURCE])
    merged, seen = [], set()
    for i in range(PER_SOURCE):
        for items in per_feed:
            if i < len(items):
                s = items[i]
                topic = " ".join(re.findall(r"[a-z]+", s["title"].lower())[:2])
                if topic in seen:
                    continue
                seen.add(topic)
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
