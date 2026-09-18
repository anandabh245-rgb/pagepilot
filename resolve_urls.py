import json
from googlenewsdecoder import gnewsdecoder

INPUT_FILE = "data/stories.json"
OUTPUT_FILE = "data/resolved_urls.json"

with open(INPUT_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)

stories = data.get("stories", [])

results = []

for story in stories[:5]:

    google_url = story.get("link", "")

    print()
    print("Resolving:")
    print(story.get("title", ""))

    try:
        result = gnewsdecoder(
            google_url,
            interval=1
        )

        if result.get("status"):
            original_url = result["decoded_url"]
            print("Original URL:")
            print(original_url)
        else:
            original_url = google_url
            print("Could not decode:")
            print(result.get("message", "Unknown error"))

    except Exception as error:
        original_url = google_url
        print("Decoder error:", error)

    results.append({
        "title": story.get("title", ""),
        "google_news_url": google_url,
        "original_url": original_url
    })


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
print("URL DECODING COMPLETE")
print("Saved to:", OUTPUT_FILE)
print("================================")
