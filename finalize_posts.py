import json
from urllib.parse import urlparse

DRAFTS_FILE = "data/drafts.json"
RESOLVED_FILE = "data/resolved_urls.json"
OUTPUT_FILE = "data/final_posts.json"


def get_domain(url):
    try:
        domain = urlparse(url).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        parts = domain.split(".")

        if len(parts) >= 2:
            return parts[-2].capitalize()

        return domain.capitalize()

    except Exception:
        return ""


with open(DRAFTS_FILE, "r", encoding="utf-8") as file:
    drafts = json.load(file)


with open(RESOLVED_FILE, "r", encoding="utf-8") as file:
    resolved = json.load(file)


final_posts = []

for draft, url_data in zip(drafts, resolved):

    original_url = url_data.get(
        "original_url",
        ""
    )

    source = get_domain(original_url)

    final_posts.append({
        "headline": draft.get("headline", ""),
        "post": draft.get("post", ""),
        "source": source,
        "source_url": original_url,
        "original_title": url_data.get(
            "title",
            ""
        )
    })


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        final_posts,
        file,
        indent=2,
        ensure_ascii=False
    )


print()
print("================================")
print("FINAL POSTS CREATED")
print("Posts:", len(final_posts))
print("Saved to:", OUTPUT_FILE)
print("================================")
