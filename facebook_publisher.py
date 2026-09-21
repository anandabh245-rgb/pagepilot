import json
import os
import sys
import urllib.parse
import urllib.request

FINAL_POSTS = "data/final_posts.json"

PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
GRAPH_VERSION = os.environ.get("META_GRAPH_VERSION", "v23.0")


def publish_to_facebook(post):
    if not PAGE_ID:
        raise RuntimeError("FACEBOOK_PAGE_ID secret is missing")

    if not PAGE_ACCESS_TOKEN:
        raise RuntimeError("FACEBOOK_PAGE_ACCESS_TOKEN secret is missing")

    message = post.get("post", "").strip()
    source_url = post.get("source_url", "").strip()

    if not message:
        raise RuntimeError("The selected post has no text")

    data = {
        "message": message,
        "access_token": PAGE_ACCESS_TOKEN,
    }

    # Add the original article link when available.
    if source_url:
        data["link"] = source_url

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{PAGE_ID}/feed"

    encoded = urllib.parse.urlencode(data).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=encoded,
        method="POST",
        headers={
            "User-Agent": "PagePilot/1.0"
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

        print("================================")
        print("FACEBOOK PUBLISH SUCCESS")
        print("================================")
        print(json.dumps(result, indent=2))
        print("================================")

        return result

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")

        print("================================")
        print("FACEBOOK PUBLISH FAILED")
        print("================================")
        print("HTTP status:", error.code)
        print(body)
        print("================================")

        raise


def main():
    print("================================")
    print("       PAGEPILOT PUBLISHER")
    print("================================")

    if not os.path.exists(FINAL_POSTS):
        raise RuntimeError(f"Missing {FINAL_POSTS}")

    with open(FINAL_POSTS, "r", encoding="utf-8") as file:
        posts = json.load(file)

    if not isinstance(posts, list) or not posts:
        raise RuntimeError("No posts found in data/final_posts.json")

    # Publish the first generated post.
    post = posts[0]

    print("Headline:", post.get("headline", ""))
    print("Source:", post.get("source", ""))
    print()

    publish_to_facebook(post)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("ERROR:", error)
        sys.exit(1)
