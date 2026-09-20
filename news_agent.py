import json
import os
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=US+celebrity+entertainment&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Hollywood+celebrity&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=US+nature+wildlife&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=US+weather+natural+disaster&hl=en-US&gl=US&ceid=US:en",
]

OUTPUT_FILE = "data/stories.json"


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_feed(url):
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "PagePilot/1.0"}
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read()

        root = ET.fromstring(data)

        stories = []

        for item in root.findall(".//item")[:10]:
            title = clean_text(
                item.findtext("title", "")
            )

            description = clean_text(
                item.findtext("description", "")
            )

                        link = item.findtext("link", "")

            source_element = item.find("source")
            publisher = ""

            if source_element is not None:
                publisher = clean_text(
                    source_element.text or ""
                )

            pub_date = item.findtext(
                "pubDate",
                ""
            )

            if title:
                   stories.append({
                    "title": title,
                    "description": description,
                    "link": link,
                    "published": pub_date,
                    "publisher": publisher
                })

        return stories

    except Exception as error:
        print("Feed error:", error)
        return []


def remove_duplicates(stories):
    seen = set()
    result = []

    for story in stories:
        key = story["title"].lower().strip()

        if key not in seen:
            seen.add(key)
            result.append(story)

    return result


def main():
    print("================================")
    print("       PAGEPILOT NEWS AGENT")
    print("================================")

    all_stories = []

    for feed in RSS_FEEDS:
        print("Reading:", feed)
        all_stories.extend(get_feed(feed))

    all_stories = remove_duplicates(all_stories)

    # Keep the newest/first 30 stories.
    all_stories = all_stories[:30]

    os.makedirs("data", exist_ok=True)

    output = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "story_count": len(all_stories),

        "stories": all_stories
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("Stories collected:", len(all_stories))
    print("Saved to:", OUTPUT_FILE)
    print("================================")


if __name__ == "__main__":
    main()
