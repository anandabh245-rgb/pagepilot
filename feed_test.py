import json, re, sys, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

FEEDS = {
    "screenrant": "https://screenrant.com/feed/",
    "screenrant_comics": "https://screenrant.com/feed/comics/",
    "collider": "https://collider.com/feed/",
    "cbr": "https://www.cbr.com/feed/",
    "comicbook": "https://comicbook.com/feed/",
    "comicbook_marvel": "https://comicbook.com/category/marvel/feed/",
    "comicbook_starwars": "https://comicbook.com/category/starwars/feed/",
    "slashfilm": "https://feeds.feedburner.com/slashfilm",
    "denofgeek": "https://www.denofgeek.com/feed/",
    "bleedingcool": "https://bleedingcool.com/feed/",
    "gizmodo": "https://gizmodo.com/feed",
}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"
NICHE = re.compile(r"marvel|mcu|avengers|spider-man|x-men|deadpool|wolverine|iron man|"
                   r"captain america|black panther|guardians|fantastic four|doctor strange|"
                   r"star wars|mandalorian|jedi|andor|skywalker|lucasfilm|grogu|darth|ahsoka|"
                   r"superman|batman|joker|justice league|wonder woman|aquaman|dc studios|"
                   r"superhero|the boys|invincible|peacemaker", re.I)


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, r.read().decode("utf-8", errors="replace")


def strip(html):
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def article_words(html):
    paras = re.findall(r"(?is)<p[^>]*>(.*?)</p>", html)
    return len(" ".join(strip(p) for p in paras).split())


out = {"tested_at": datetime.now(timezone.utc).isoformat(), "feeds": {}}
for name, url in FEEDS.items():
    info = {"url": url}
    try:
        status, body = get(url)
        info["feed_status"] = status
        root = ET.fromstring(body)
        items = list(root.iter("item"))
        info["items"] = len(items)
        info["niche_items"] = sum(
            1 for it in items if NICHE.search((it.findtext("title") or "")))
        samples = []
        for it in items[:2]:
            link = (it.findtext("link") or "").strip()
            s = {"title": (it.findtext("title") or "")[:90], "link": link}
            try:
                st, html = get(link)
                s["page_status"] = st
                s["page_words"] = article_words(html)
            except urllib.error.HTTPError as e:
                s["page_status"] = e.code
            except Exception as e:
                s["page_error"] = str(e)[:80]
            samples.append(s)
        info["article_samples"] = samples
    except urllib.error.HTTPError as e:
        info["feed_status"] = e.code
    except Exception as e:
        info["error"] = str(e)[:120]
    out["feeds"][name] = info
    print(name, json.dumps({k: v for k, v in info.items() if k != "article_samples"}))

with open("data/feed_test.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
