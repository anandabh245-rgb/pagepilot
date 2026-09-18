import json
import os
import time
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
You are the senior social-media editor for a professional US entertainment and news Facebook Page.

Your job is to transform the supplied news story into an ORIGINAL Facebook post that feels written by a real human editor.

IMPORTANT:
- Use ONLY facts contained in the supplied story.
- Never invent facts, quotes, reactions, numbers, dates, names, or details.
- Do not exaggerate.
- Do not use misleading clickbait.
- Do not state rumors or allegations as confirmed facts.
- Do not pretend you witnessed the event.
- Do not copy sentences from the source.
- Do not begin with generic phrases such as "Big news!", "Breaking news!", or "Exciting news!"
- Avoid corporate or robotic language.
- Do not say "Check out the details below."
- Do not tell readers to "read the article" unless it naturally fits.
- The post should provide useful information by itself.
- Write for a US Facebook audience.
- Use a conversational but professional tone.
- Make the opening sentence interesting without being sensational.
- Keep the post around 60–120 words.
- Use short paragraphs for mobile reading.
- Emojis are optional and should be used sparingly.
- End naturally. A simple question is allowed only when it genuinely fits the story.
- Do not add hashtags unless they are clearly useful.
- Preserve uncertainty when the source itself is uncertain.

The result must contain:
1. A natural headline.
2. A polished Facebook post.
3. The source URL.

Return ONLY valid JSON in exactly this format:

{{
  "headline": "...",
  "post": "...",
  "source": "{story.get("link", "")}"
}}

NEWS STORY:

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

    result = None

    for attempt in range(5):

        try:
            with urllib.request.urlopen(
                request,
                timeout=60
            ) as response:

                result = json.loads(
                    response.read().decode("utf-8")
                )

            break

        except urllib.error.HTTPError as e:

            if e.code in (408, 429, 500, 502, 503, 504) and attempt < 4:

                wait_time = 5 * (2 ** attempt)

                print(
                    f"Gemini temporarily unavailable "
                    f"(HTTP {e.code}). "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:

                body = e.read().decode(
                    "utf-8",
                    errors="replace"
                )

                raise RuntimeError(
                    f"Gemini API HTTP {e.code}: "
                    f"{body[:1000]}"
                )


    if result is None:
        raise RuntimeError(
            "Gemini request failed after all retries."
        )


    if "candidates" not in result:
        raise RuntimeError(
            "Gemini returned no candidates: "
            + json.dumps(result)[:1000]
        )


    text = (
        result["candidates"][0]
        ["content"]
        ["parts"][0]
        ["text"]
        .strip()
    )


    return json.loads(text)


with open(INPUT_FILE, "r", encoding="utf-8") as f:

    data = json.load(f)


if isinstance(data, dict):

    stories = data.get("stories", [])

else:

    stories = data


drafts = []


for story in stories[:2]:

    draft = ask_gemini(story)

    draft["original_title"] = story.get(
        "title",
        ""
    )

    draft["original_url"] = story.get(
        "link",
        ""
    )

    drafts.append(draft)

    print(
        "Created:",
        story.get("title", "")
    )


if not drafts:

    raise RuntimeError(
        "No Facebook drafts were generated."
    )


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        drafts,
        f,
        indent=2,
        ensure_ascii=False
    )


print(
    f"Created {len(drafts)} Facebook drafts."
)
