import json
import os
import urllib.request
import urllib.error

INPUT_FILE = "data/stories.json"
OUTPUT_FILE = "data/drafts.json"

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY secret is missing")

MODEL = "gemini-3.6-flash"

API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL}:generateContent"
)


def ask_gemini(story):

    prompt = f"""
You are a professional US Facebook Page editor.

Create ONE natural Facebook post using ONLY the information provided.

Rules:
- Do not invent facts.
- Do not invent quotes.
- Do not invent dates or numbers.
- Do not present rumors as confirmed facts.
- Clearly identify unconfirmed information.
- Do not use misleading clickbait.
- Sound like a real human Facebook editor.
- Keep it engaging and concise.
- Target a US audience.
- Include the original source URL.
- Return ONLY valid JSON.

Return exactly:

{{
  "headline": "...",
  "post": "...",
  "source": "..."
}}

STORY:

Title: {story.get("title", "")}

Description: {story.get("description", "")}

Published: {story.get("published", "")}

Source URL: {story.get("link", "")}
"""

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Gemini API HTTP {e.code}: {body[:1000]}"
        )

    if "candidates" not in result:
        raise RuntimeError(
            "Gemini returned no candidates: "
            + json.dumps(result)[:1000]
        )

    text = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    return json.loads(text)


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

if isinstance(data, dict):
    stories = data.get("stories", [])
else:
    stories = data

drafts = []

# Start with only 2 stories for testing
for story in stories[:2]:

    draft = ask_gemini(story)

    draft["original_title"] = story.get("title", "")
    draft["original_url"] = story.get("link", "")

    drafts.append(draft)

    print("Created:", story.get("title", ""))


if not drafts:
    raise RuntimeError("No Facebook drafts were generated.")


with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(
        drafts,
        f,
        indent=2,
        ensure_ascii=False
    )

print(f"Created {len(drafts)} Facebook drafts.")
