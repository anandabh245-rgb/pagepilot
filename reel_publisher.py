import json, os, re, subprocess, sys
import urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import card_deck  # patches the sad-story word list used by classify()
from card_maker import classify
from reel_maker import make_reel
import media_helpers

FINAL = "data/final_posts.json"
POSTED = "data/posted.json"
LOG = "data/reels_posted.json"
WEBHOOK = os.environ.get("MAKE_WEBHOOK_URL", "").strip()
DRY = os.environ.get("DRY_RUN", "true").strip().lower() != "false"
ENFORCE_GAP = os.environ.get("ENFORCE_GAP", "false").strip().lower() == "true"
MIN_GAP_MIN = int(os.environ.get("MIN_GAP_MIN", "130"))
DAILY_MAX = int(os.environ.get("DAILY_MAX", "5"))
# Post only in these hours of the day, US Eastern time (handles daylight saving automatically).
# 7 = morning scroll, 12 = lunch, 14 = early afternoon, 17 = after work, 20 = prime evening
SLOT_HOURS_ET = {int(x) for x in os.environ.get("SLOT_HOURS_ET", "7,12,14,17,20").split(",") if x.strip()}
REPO = os.environ.get("GITHUB_REPOSITORY", "anandabh245-rgb/pagepilot")
GIT = ["git", "-c", "user.name=PagePilot Bot",
       "-c", "user.email=pagepilot@users.noreply.github.com"]

# capitalised words that start headlines but are not names
STOP = {"The", "This", "That", "These", "Why", "How", "What", "When", "Who", "Where",
        "After", "Before", "Fans", "Report", "Reports", "Breaking", "Watch", "New",
        "Just", "Here", "His", "Her", "Their", "Our", "Your", "And", "But", "For"}


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def too_soon(log):
    now = datetime.now(timezone.utc)
    now_et = now.astimezone(ZoneInfo("America/New_York"))
    if now_et.hour not in SLOT_HOURS_ET:
        return True, "outside USA posting slots (now %s ET)" % now_et.strftime("%I:%M %p")
    times = []
    for e in log:
        try:
            times.append(datetime.fromisoformat(e["posted_at"]))
        except Exception:
            pass
    if not times:
        return False, ""
    mins = int((now - max(times)).total_seconds() // 60)
    if mins < MIN_GAP_MIN:
        return True, "last Reel was only %d minutes ago" % mins
    if len([t for t in times if now - t < timedelta(hours=24)]) >= DAILY_MAX:
        return True, "daily Reel limit reached"
    return False, ""


def key(p):
    return (p.get("source_url") or p.get("headline") or "").strip()


def caption(p, credit=""):
    text = p["post"].strip()
    host = urllib.parse.urlparse(p.get("source_url", "")).netloc.replace("www.", "")
    if host and "google." not in host:
        text += "\n\nSource: " + host
    if credit:
        text += "\n" + credit
    return text


def find_photo(headline, mood):
    """Free-licensed photo for the story. Returns (path, credit) or (None, None)."""
    out = "data/reel_tmp/photo.jpg"
    os.makedirs("data/reel_tmp", exist_ok=True)
    names = re.findall(r"\b[A-Z][a-zA-Z'\-]+(?:\s[A-Z][a-zA-Z'\-]+){1,2}\b", headline)
    tried = []
    for n in names:
        if n.split()[0] in STOP or n in tried:
            continue
        tried.append(n)
        path, credit = media_helpers.wikimedia_image(n, out, strict=True)
        if path:
            print("Photo found for:", n)
            return path, credit
        if len(tried) >= 3:
            break
    theme = "galaxy nebula" if mood == "space" else "red carpet premiere"
    return media_helpers.get_image(theme, fallback_theme=theme, out_path=out)


def host_video(path):
    """Put the video alone on the 'media' branch (replaced each time, so the repo stays small)."""
    name = os.path.basename(path)
    blob = subprocess.run(GIT + ["hash-object", "-w", path], check=True,
                          capture_output=True, text=True).stdout.strip()
    tree = subprocess.run(GIT + ["mktree"], check=True, capture_output=True, text=True,
                          input="100644 blob %s\t%s\n" % (blob, name)).stdout.strip()
    commit = subprocess.run(GIT + ["commit-tree", tree, "-m", "reel"], check=True,
                            capture_output=True, text=True).stdout.strip()
    subprocess.run(GIT + ["push", "-f", "origin", "%s:refs/heads/media" % commit], check=True)
    return "https://raw.githubusercontent.com/%s/media/%s" % (REPO, name)


def main():
    print("Mode:", "DRY RUN (nothing sent)" if DRY else "LIVE")
    print("Make webhook secret:", "yes" if WEBHOOK else "NO")
    if not DRY and not WEBHOOK:
        raise RuntimeError("MAKE_WEBHOOK_URL secret is missing")
    log = load(LOG, [])
    if ENFORCE_GAP and not DRY:
        wait, why = too_soon(log)
        if wait:
            print("Not time yet:", why)
            return 0
    posts = load(FINAL, [])
    photo_done = {e.get("key") for e in load(POSTED, []) if isinstance(e, dict)}
    reel_done = {e.get("key") for e in log if isinstance(e, dict)}
    pool = [p for p in posts if p.get("kind") == "card" and key(p) not in photo_done
            and key(p) not in reel_done and len((p.get("post") or "")) >= 150]
    print("Stories ready for a Reel:", len(pool))
    if not pool:
        return 0
    p = pool[0]
    text = " ".join(p["headline"].upper().split())
    mood, label, hook, face = classify(text)
    print("Making Reel for:", p["headline"])
    os.makedirs("data/reel_tmp", exist_ok=True)

    # real free photo instead of the emoji (skipped for sad stories)
    photo, credit = None, None
    if mood != "somber":
        try:
            photo, credit = find_photo(p["headline"], mood)
        except Exception as e:
            print("Photo search failed, using emoji look:", e)
    print("Photo credit:", credit or "none (using emoji look)")

    name = "reel_%s.mp4" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join("data/reel_tmp", name)
    make_reel(p["headline"], p["post"], label, mood, face, hook, path, photo_path=photo)
    print("Video size KB:", os.path.getsize(path) // 1024)
    if DRY:
        os.replace(path, "data/reel_preview.mp4")
        print("[dry run] saved data/reel_preview.mp4, not sent")
        return 0
    url = host_video(path)
    print("Video hosted at:", url)
    payload = {"video_url": url, "caption": caption(p, credit), "title": p["headline"][:90]}
    req = urllib.request.Request(
        WEBHOOK, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "PagePilot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            print("SENT to Make:", r.status, r.read().decode(errors="replace")[:100])
    except urllib.error.HTTPError as e:
        print("SEND FAILED", e.code, e.read().decode(errors="replace")[:200])
        return 1
    log.append({"key": key(p), "headline": p["headline"],
                "posted_at": datetime.now(timezone.utc).isoformat()})
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)
