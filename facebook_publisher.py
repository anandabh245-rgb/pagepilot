import json, os, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

FINAL = "data/final_posts.json"
LOG = "data/posted.json"
PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
VER = os.environ.get("META_GRAPH_VERSION", "v25.0")
DRY = os.environ.get("DRY_RUN", "true").strip().lower() != "false"
MAX_POSTS = int(os.environ.get("MAX_POSTS", "2"))


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def key(p):
    return (p.get("source_url") or p.get("headline") or "").strip()


def publish(p):
    data = {"message": p["post"].strip(), "access_token": TOKEN}
    if p.get("source_url"):
        data["link"] = p["source_url"].strip()
    req = urllib.request.Request(
        f"https://graph.facebook.com/{VER}/{PAGE_ID}/feed",
        data=urllib.parse.urlencode(data).encode(),
        method="POST", headers={"User-Agent": "PagePilot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print("FAILED", e.code, e.read().decode(errors="replace"))
        raise


def main():
    print("Mode:", "DRY RUN (nothing posted)" if DRY else "LIVE")
    print("Page ID secret:", "yes" if PAGE_ID else "NO")
    print("Token secret:", "yes" if TOKEN else "NO")
    if not DRY and not (PAGE_ID and TOKEN):
        raise RuntimeError("Facebook secrets missing")
    posts = load(FINAL, [])
    log = load(LOG, [])
    done = {e.get("key") for e in log if isinstance(e, dict)}
    todo = [p for p in posts if key(p) and key(p) not in done
            and 40 <= len((p.get("post") or "").strip()) <= 2000]
    print("New posts:", len(todo), "| limit:", MAX_POSTS)
    fails = 0
    for p in todo[:MAX_POSTS]:
        print("\n---", p.get("headline", ""), "\n" + p["post"].strip())
        if DRY:
            print("[dry run] not posted")
            continue
        try:
            res = publish(p)
            print("POSTED", res.get("id"))
            log.append({"key": key(p), "headline": p.get("headline", ""),
                        "facebook_id": res.get("id"),
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
