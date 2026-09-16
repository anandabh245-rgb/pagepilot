import json
import os
import urllib.request
import urllib.error

INPUT_FILE = "data/stories.json"
OUTPUT_FILE = "data/drafts.json"

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY secret is missing")

MODEL = "gemini-2.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"


def ask_gemini(story):
    prompt = f"""
You are the writing editor for a professional US Facebook Page.

Write ONE natural Facebook post based ONLY on the information supplied below.

IMPORTANT RULES:
- Do not invent facts.
- Do not invent quotes.
- Do not invent dates or numbers.
- Do not present rumors as confirmed facts.
- If something is unconfirmed, clearly say so.
- Do not use sensational or misleading clickbait.
- Write like a real human social-media editor, not like an AI.
- Keep it engaging but factual.
- Target a US Facebook audience.
- Include the original source link.
- Do not use hashtags unless they genuinely help.
- Return ONLY valid JSON.

Return this exact structure:

{{
  "headline": "...",
  "post": "...",
  "source": "..."
}}

STORY:
Title: {story.get("title", "")}
Description: {story.get("description", "")}
Published: {story.get("pubDate", "")}
Source URL: {story.get("link", "")}
"""

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))

    text = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Remove markdown code fences if Gemini adds them
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    stories = json.load(f)

drafts = []

# Start with only 5 stories to keep the free API usage small.
for story in stories[:5]:
    try:
        draft = ask_gemini(story)

        draft["original_title"] = story.get("title", "")
        draft["original_url"] = story.get("link", "")

        drafts.append(draft)

        print("Created:", story.get("title", ""))

    except Exception as e:
        print("Skipped story:", story.get("title", ""))
        print("Error:", e)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(drafts, f, indent=2, ensure_ascii=False)

print(f"Created {len(drafts)} Facebook drafts.")
