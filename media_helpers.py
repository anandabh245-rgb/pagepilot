"""
media_helpers.py - random music + free-licensed images for reels.

Setup (all from phone via GitHub web editor):
1. Create a folder `music/` in your repo and upload 5-10 royalty-free .mp3 files.
2. (Optional) Add a free Pexels API key as a GitHub secret named PEXELS_API_KEY.
3. `pip install requests` must be in your requirements.txt.
"""
import os
import random
import re
import subprocess
import requests

MUSIC_DIR = "music"
UA = {"User-Agent": "MarvelStarWarsPageBot/1.0 (contact: your-email@example.com)"}

# Licenses that are safe to reuse (attribution required for CC BY / CC BY-SA)
OK_LICENSES = ("cc0", "cc by", "cc-by", "public domain", "pd")


# ---------------------------------------------------------------- MUSIC
def pick_music(state_file=".last_music"):
    """Random track from music/, never the same one twice in a row."""
    tracks = [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith((".mp3", ".m4a", ".wav"))]
    if not tracks:
        raise RuntimeError("No music files found in music/ folder")
    last = open(state_file).read().strip() if os.path.exists(state_file) else ""
    choices = [t for t in tracks if t != last] or tracks
    pick = random.choice(choices)
    open(state_file, "w").write(pick)
    return os.path.join(MUSIC_DIR, pick)


# ---------------------------------------------------------------- IMAGES
def _clean(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()


def wikimedia_image(query, out_path="bg.jpg", strict=False):
    """Search Wikimedia Commons for a freely licensed photo.
    Returns (path, credit_text) or (None, None)."""
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 15,
        "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1080,
    }
    try:
        r = requests.get("https://commons.wikimedia.org/w/api.php",
                         params=params, headers=UA, timeout=30)
        pages = list(r.json().get("query", {}).get("pages", {}).values())
    except Exception:
        return None, None
    random.shuffle(pages)
    for p in pages:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        lic = _clean(meta.get("LicenseShortName", {}).get("value", "")).lower()
        if not any(lic.startswith(k) for k in OK_LICENSES):
            continue
        if info.get("width", 0) < 800:
            continue
        if strict and query.split()[-1].lower() not in p.get("title", "").lower():
            continue  # file name must contain the person's last name
        url = info.get("thumburl") or info.get("url")
        img = requests.get(url, headers=UA, timeout=60)
        if img.status_code != 200:
            continue
        open(out_path, "wb").write(img.content)
        author = _clean(meta.get("Artist", {}).get("value", "Unknown"))
        credit = f"Photo: {author} / Wikimedia Commons ({lic.upper()})"
        return out_path, credit
    return None, None


def pexels_image(query, out_path="bg.jpg"):
    """Free stock photo fallback (no celebrities, good for moods/themes)."""
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None, None
    try:
        r = requests.get("https://api.pexels.com/v1/search",
                         params={"query": query, "per_page": 15, "orientation": "portrait"},
                         headers={"Authorization": key}, timeout=30)
        photos = r.json().get("photos", [])
        if not photos:
            return None, None
        p = random.choice(photos)
        img = requests.get(p["src"]["large2x"], timeout=60)
        open(out_path, "wb").write(img.content)
        return out_path, f"Photo: {p['photographer']} / Pexels"
    except Exception:
        return None, None


def get_image(keywords, fallback_theme="space galaxy cinematic", out_path="bg.jpg"):
    """Try: exact topic on Commons -> theme on Pexels -> theme on Commons."""
    for fn, q in ((wikimedia_image, keywords),
                  (pexels_image, fallback_theme),
                  (wikimedia_image, fallback_theme)):
        path, credit = fn(q, out_path)
        if path:
            return path, credit
    return None, None


# ---------------------------------------------------------------- VIDEO
def make_reel(image_path, music_path, out_path="reel.mp4", seconds=12):
    """Still image (slow zoom) + music -> 1080x1920 vertical mp4.
    Skip this if your existing pipeline already builds the video; just
    swap in image_path and music_path there."""
    vf = ("scale=1188:2112:force_original_aspect_ratio=increase,"
          "crop=1188:2112,"
          "zoompan=z='min(zoom+0.0008,1.12)':d=1:s=1080x1920:fps=30,"
          "format=yuv420p")
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", music_path,
           "-t", str(seconds), "-vf", vf,
           "-af", f"afade=t=out:st={seconds-1}:d=1",
           "-c:v", "libx264", "-c:a", "aac", "-shortest", out_path]
    subprocess.run(cmd, check=True)
    return out_path


if __name__ == "__main__":
    img, credit = get_image("Chris Hemsworth")
    print(img, credit)
    print(pick_music())
    
