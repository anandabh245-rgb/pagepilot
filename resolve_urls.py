import json
import urllib.request

INPUT_FILE = "data/stories.json"
OUTPUT_FILE = "data/resolved_urls.json"


def resolve_url(url):
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            return response.geturl()

    except Exception as error:
        print("Could not resolve:", url)
        print("Reason:", error)
        return url


with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    data = json.load(file)


stories = data.get("stories", [])


results = []

for story in stories[:5]:

    google_url = story.get("link", "")

    print()
    print("Resolving:")
    print(google_url)

    final_url = resolve_url(google_url)

    results.append({
        "title": story.get("title", ""),
        "google_news_url": google_url,
        "resolved_url": final_url
    })

    print("Result:")
    print(final_url)


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        results,
        file,
        indent=2,
        ensure_ascii=False
    )


print()
print("================================")
print("URL RESOLUTION COMPLETE")
print("Saved to:", OUTPUT_FILE)
print("Stories tested:", len(results))
print("================================")
