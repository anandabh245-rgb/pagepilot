import json, os, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

from PIL import Image

try:
    from card_deck import make_card
except Exception as e:
    print("Cards disabled:", e)
    make_card = None

FINAL = "data/final_posts.json"
LOG = "data/posted.json"
WEBHOOK = os.environ.get("MAKE_WEBHOOK_URL", "").strip()
DRY = os.environ.get("DRY_RUN", "true").strip().lower() != "false"
MAX_POSTS = int(os.environ.get("MAX_POSTS", "1"))
CARD_DIR = "data/preview"
OUTBOX = "data/outbox"
REPO = os.environ.get("GITHUB_REPOSITORY", "anandabh245-rgb/pagepilot")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
GIT = ["git", "-c", "user.name=PagePilot Bot",
       "-c", "user.email=pagepilot@users.noreply.github.com"]


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def key(p):
    return (p.get("source_url") or p.get("headline") or "").strip()


def make_caption(p):
    text = p["post"].strip()
    host = urllib.parse.urlparse(p.get("source_url", "")).netloc
    host = host.replace("www.", "")
    if host and "google." not in host:
        text += "\n\nSource: " + host
    return text


def host_card(card_png):
    """Save the card as a JPEG in the repo and push it so Make can download it."""
    os.makedirs(OUTBOX, exist_ok=True)
    name = "card_%s.jpg" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTBOX, name)
    Image.open(card_png).convert("RGB").save(path, "JPEG", quality=88,
                                             optimize=True)
    old = sorted(f for f in os.listdir(OUTBOX) if f.endswith(".jpg"))[:-10]
    subprocess.run(GIT + ["add", path], check=True)
    for f in old:
        subprocess.run(GIT + ["rm", "-q", "--ignore-unmatch",
                              os.path.join(OUTBOX, f)], check=False)
    subprocess.run(GIT + ["commit", "-m", "Add card for Make"], check=True)
    subprocess.run(GIT + ["pull", "--rebase", "--autostash"], check=True)
    subprocess.run(GIT + ["push", "origin", "HEAD"], check=True)
    time.sleep(10)
    return "https://raw.githubusercontent.com/%s/%s/%s" % (REPO, BRANCH, path)


def send_to_make(p, image_url):
    payload = {
        "image_url": image_url,
        "caption": make_caption(p),
    }
    req = urllib.request.Request(
        WEBHOOK, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json",
                 "User-Agent": "PagePilot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode(errors="replace")[:200]
    except urllib.error.HTTPError as e:
        print("SEND FAILED", e.code, e.read().decode(errors="replace")[:300])
        raise


def main():
    print("Mode:", "DRY RUN (nothing sent)" if DRY else "LIVE")
    print("Make webhook secret:", "yes" if WEBHOOK else "NO")
    print("Cards:", "on" if make_card else "off")
    if not DRY and not WEBHOOK:
        raise RuntimeError("MAKE_WEBHOOK_URL secret is missing")
    if not DRY and not make_card:
        raise RuntimeError("Cards are off, refusing to post")
    posts = load(FINAL, [])
    log = load(LOG, [])
    done = {e.get("key") for e in log if isinstance(e, dict)}
    todo = [p for p in posts if key(p) and key(p) not in done
            and 40 <= len((p.get("post") or "").strip()) <= 2000]
    print("New posts:", len(todo), "| limit:", MAX_POSTS)
    fails = 0
    for i, p in enumerate(todo[:MAX_POSTS]):
        print("\n---", p.get("headline", ""), "\n" + make_caption(p))
        card_path = None
        if make_card:
            try:
                os.makedirs(CARD_DIR, exist_ok=True)
                card_path = make_card(p.get("headline", ""),
                                      os.path.join(CARD_DIR, "card_%d.png" % i))
                print("Card created:", card_path)
            except Exception as e:
                print("Card failed:", e)
        if DRY:
            print("[dry run] not sent")
            continue
        if not card_path:
            fails += 1
            print("ERROR: no card, skipping this post")
            continue
        try:
            image_url = host_card(card_path)
            print("Card hosted at:", image_url)
            status, body = send_to_make(p, image_url)
            print("SENT to Make:", status, body)
            log.append({"key": key(p), "headline": p.get("headline", ""),
                        "sent_via": "make",
                        "posted_at": datetime.now(timezone.utc).isoformat()})
            with open(LOG, "w", encoding="utf-8") as f:
                json.dump(log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            fails += 1
            print("ERROR:", e)
    return 1 if fails else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)
