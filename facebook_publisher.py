import json, os, sys, uuid
import urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

try:
    from card_art import make_card
except Exception as e:
    print("Cards disabled:", e)
    make_card = None

FINAL = "data/final_posts.json"
LOG = "data/posted.json"
PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
VER = os.environ.get("META_GRAPH_VERSION", "v25.0")
DRY = os.environ.get("DRY_RUN", "true").strip().lower() != "false"
MAX_POSTS = int(os.environ.get("MAX_POSTS", "2"))
CARD_DIR = "data/preview" if DRY else "cards"


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def key(p):
    return (p.get("source_url") or p.get("headline") or "").strip()


def call(path, fields, files=None):
    url = "https://graph.facebook.com/%s/%s" % (VER, path)
    headers = {"User-Agent": "PagePilot/1.0"}
    if files:
        boundary = uuid.uuid4().hex
        body = b""
        for k, v in fields.items():
            body += ('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
                     % (boundary, k, v)).encode()
        for k, (name, data, ctype) in files.items():
            body += ('--%s\r\nContent-Disposition: form-data; name="%s"; '
                     'filename="%s"\r\nContent-Type: %s\r\n\r\n'
                     % (boundary, k, name, ctype)).encode() + data + b"\r\n"
        body += ("--%s--\r\n" % boundary).encode()
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundary
    else:
        body = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print("FAILED", e.code, e.read().decode(errors="replace"))
        raise


def publish(p, card_path):
    text = p["post"].strip()
    if card_path:
        try:
            caption = text
            if p.get("source"):
                caption += "\n\nSource: " + p["source"].strip()
            with open(card_path, "rb") as f:
                img = f.read()
            return call(PAGE_ID + "/photos",
                        {"caption": caption, "access_token": TOKEN},
                        {"source": ("card.png", img, "image/png")})
        except Exception as e:
            print("Photo post failed, falling back to text:", e)
    fields = {"message": text, "access_token": TOKEN}
    if p.get("source_url"):
        fields["link"] = p["source_url"].strip()
    return call(PAGE_ID + "/feed", fields)


def main():
    print("Mode:", "DRY RUN (nothing posted)" if DRY else "LIVE")
    print("Page ID secret:", "yes" if PAGE_ID else "NO")
    print("Token secret:", "yes" if TOKEN else "NO")
    print("Cards:", "on" if make_card else "off")
    if not DRY and not (PAGE_ID and TOKEN):
        raise RuntimeError("Facebook secrets missing")
    posts = load(FINAL, [])
    log = load(LOG, [])
    done = {e.get("key") for e in log if isinstance(e, dict)}
    todo = [p for p in posts if key(p) and key(p) not in done
            and 40 <= len((p.get("post") or "").strip()) <= 2000]
    print("New posts:", len(todo), "| limit:", MAX_POSTS)
    fails = 0
    for i, p in enumerate(todo[:MAX_POSTS]):
        print("\n---", p.get("headline", ""), "\n" + p["post"].strip())
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
            print("[dry run] not posted")
            continue
        try:
            res = publish(p, card_path)
            fb_id = res.get("post_id") or res.get("id")
            print("POSTED", fb_id)
            log.append({"key": key(p), "headline": p.get("headline", ""),
                        "facebook_id": fb_id,
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
