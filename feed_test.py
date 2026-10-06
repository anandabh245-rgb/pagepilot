import json, re, sys, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

FEEDS = {
    "variety": "https://variety.com/feed/",
    "hollywoodreporter": "https://www.hollywoodreporter.com/feed/",
    "deadline": "https://deadline.com/feed/",
    "eonline": "https://www.eonline.com/syndication/feeds/rssfeeds/topstories.xml",
    "rollingstone": "https://www.rollingstone.com/feed/",
    "pagesix": "https://pagesix.com/feed/",
    "tmz": "https://www.tmz.com/rss.xml",
}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"


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
    text = " ".join(strip(p) for p in paras)
    return len(text.split())


out = {"tested_at": datetime.now(timezone.utc).isoformat(), "feeds": {}}
for name, url in FEEDS.items():
    info = {"url": url}
    try:
        status, body = get(url)
        info["feed_status"] = status
        root = ET.fromstring(body)
        items = list(root.iter("item"))
        info["items"] = len(items)
        d_len, c_len = [], []
        for it in items[:10]:
            d_len.append(len(strip(it.findtext("description") or "").split()))
            c_len.append(len(strip(it.findtext(CONTENT) or "").split()))
        info["avg_description_words"] = round(sum(d_len) / max(1, len(d_len)))
        info["avg_full_content_words_in_feed"] = round(sum(c_len) / max(1, len(c_len)))
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
