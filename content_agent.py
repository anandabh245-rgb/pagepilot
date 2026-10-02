import json, os, time, urllib.error, urllib.request

INPUT_FILE = "data/stories.json"
OUTPUT_FILE = "data/drafts.json"
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY secret is missing")

MODEL = "gemini-3.5-flash-lite"
API_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
           + MODEL + ":generateContent")

RULES = """You edit a popular US entertainment Facebook Page covering Hollywood celebrity news, movies and TV.
Turn the story below into an ORIGINAL Facebook post.

FACTS
- Use ONLY facts found in the story. Never invent quotes, numbers, dates, names or reactions.
- Rumors or reports stay "reportedly" or "according to". Never present allegations as confirmed.
- Do not copy sentences from the source.

STYLE
- First line is a short hook (under 12 words) that names the star, show or movie. Create curiosity without misleading clickbait. Never start with "Breaking news" or "Big news".
- Frame the story around the stars, shows or films involved, where the story supports it.
- 50 to 90 words in 2 or 3 short paragraphs. Plain, friendly language, like telling a friend who loves entertainment.
- At most 1 or 2 emojis.
- End with ONE clear question that invites opinions, predictions or favorites.
- Put exactly 3 relevant hashtags on the final line.

EXAMPLE of the energy we want (invented, never reuse its facts):
Headline: Fans are NOT ready for this casting news 👀
Post: Fans of the hit drama just got a surprise: a fan-favorite star is reportedly returning for the next season.

The report says filming starts this fall, though the studio hasn't confirmed details yet.

Who would you love to see come back?

#TVNews #Hollywood #Drama

HEADLINE FIELD
- "headline" is NOT the news title. It is a punchy 4 to 8 word reaction line for a graphic card, like "Fans are NOT ready for this" or "This changes everything for the show". It must stay truthful to the story and never invent facts.

HEADLINE FIELD
Return ONLY valid JSON with exactly these fields, no markdown and no code fences:
{"headline": "...", "post": "...", "source": "..."}
"""


def ask_gemini(story):
    prompt = (RULES + "\nNEWS STORY:\nTitle: " + story.get("title", "")
              + "\nDescription: " + story.get("description", "")
              + "\nPublished: " + story.get("published", "")
              + "\nSource URL: " + story.get("link", "") + "\n")
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }).encode("utf-8")

    for attempt in range(5):
        req = urllib.request.Request(
            API_URL, data=body, method="POST",
            headers={"Content-Type": "application/json",
                     "x-goog-api-key": API_KEY})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                result = json.loads(r.read().decode("utf-8"))
            text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            return json.loads(text)
        except urllib.error.HTTPError as e:
            if e.code in (408, 429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(5 * 2 ** attempt)
                continue
            raise RuntimeError("Gemini HTTP %s: %s" % (
                e.code, e.read().decode(errors="replace")[:500]))
        except (urllib.error.URLError, KeyError, IndexError,
                json.JSONDecodeError) as e:
            if attempt < 4:
                print("Retrying after error:", e)
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError("Gemini failed after retries: %s" % e)


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
stories = data.get("stories", []) if isinstance(data, dict) else data

drafts = []
for story in stories[:7]:
    try:
        draft = ask_gemini(story)
    except Exception as e:
        print("Skipped:", story.get("title", ""), e)
        continue
    draft["original_title"] = story.get("title", "")
    draft["original_url"] = story.get("link", "")
    if draft.get("post", "").count("#") < 3:
        draft["post"] = draft["post"].rstrip() + "\n\n#Entertainment #Hollywood #PopCulture"
    drafts.append(draft)
    print("Created:", story.get("title", ""))

if not drafts:
    raise RuntimeError("No Facebook drafts were generated.")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(drafts, f, indent=2, ensure_ascii=False)
print("Created %d Facebook drafts." % len(drafts))
