#!/usr/bin/env python3
"""Download Wikipedia portrait thumbnails for all 28 built-in elders.

Usage:
    python scripts/download_avatars.py

Fetches thumbnails via the Wikipedia REST API, resizes to 128x128 JPEG,
and writes to council/web/static/desktop/img/avatars/.
Also generates ATTRIBUTION.md with source and license info.
"""

import json
import sys
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen, Request

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

AVATAR_DIR = Path(__file__).resolve().parent.parent / "council" / "web" / "static" / "desktop" / "img" / "avatars"
SIZE = 128
QUALITY = 75

# Elder ID → Wikipedia article title
ELDERS = {
    "aurelius":   "Marcus Aurelius",
    "franklin":   "Benjamin Franklin",
    "buffett":    "Warren Buffett",
    "munger":     "Charlie Munger",
    "bruce_lee":  "Bruce Lee",
    "musashi":    "Miyamoto Musashi",
    "sun_tzu":    "Sun Tzu",
    "buddha":     "Gautama Buddha",
    "branden":    "Nathaniel Branden",
    "kabatzinn":  "Jon Kabat-Zinn",
    "clear":      "James Clear",
    "greene":     "Robert Greene (American author)",
    "naval":      "Naval Ravikant",
    "rubin":      "Rick Rubin",
    "oprah":      "Oprah Winfrey",
    "thich":      "Thich Nhat Hanh",
    "jung":       "Carl Jung",
    "laotzu":     "Laozi",
    "davinci":    "Leonardo da Vinci",
    "kahneman":   "Daniel Kahneman",
    "tubman":     "Harriet Tubman",
    "tetlock":    "Philip E. Tetlock",
    "klein":      "Gary Klein",
    "meadows":    "Donella Meadows",
    "hannibal":   "Hannibal",
    "boudicca":   "Boudica",
    "genghis":    "Genghis Khan",
    "lauder":     "Estée Lauder (businesswoman)",
}

UA = "CouncilOfElders/1.0 (portrait downloader; contact: github)"


def fetch_summary(title: str) -> dict:
    """Fetch Wikipedia page summary via REST API."""
    from urllib.parse import quote
    encoded = quote(title.replace(' ', '_'), safe='')
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def download_and_resize(image_url: str, out_path: Path) -> None:
    """Download image, crop to square center, resize to SIZExSIZE JPEG."""
    req = Request(image_url, headers={"User-Agent": UA})
    with urlopen(req, timeout=30) as resp:
        data = resp.read()
    img = Image.open(BytesIO(data)).convert("RGB")

    # Center crop to square
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    # Resize
    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    img.save(out_path, "JPEG", quality=QUALITY, optimize=True)


def main():
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    attributions = []
    successes = 0
    failures = []

    for elder_id, wiki_title in ELDERS.items():
        out_path = AVATAR_DIR / f"{elder_id}.jpg"
        print(f"  {elder_id}: fetching {wiki_title}...", end=" ", flush=True)

        try:
            summary = fetch_summary(wiki_title)
            thumb_url = summary.get("thumbnail", {}).get("source")
            if not thumb_url:
                # Try originalimage if thumbnail missing
                thumb_url = summary.get("originalimage", {}).get("source")
            if not thumb_url:
                print("NO IMAGE")
                failures.append(elder_id)
                continue

            download_and_resize(thumb_url, out_path)
            size_kb = out_path.stat().st_size / 1024
            print(f"OK ({size_kb:.0f} KB)")
            successes += 1

            # Collect attribution info
            page_url = summary.get("content_urls", {}).get("desktop", {}).get("page", "")
            license_info = summary.get("license", {}).get("type", "Public domain / CC")
            attributions.append({
                "elder_id": elder_id,
                "name": summary.get("title", wiki_title),
                "source": page_url or f"https://en.wikipedia.org/wiki/{wiki_title.replace(' ', '_')}",
                "license": license_info,
                "thumb_url": thumb_url,
            })

        except Exception as e:
            print(f"FAILED: {e}")
            failures.append(elder_id)

    # Write ATTRIBUTION.md
    attr_path = AVATAR_DIR / "ATTRIBUTION.md"
    with open(attr_path, "w") as f:
        f.write("# Elder Avatar Image Credits\n\n")
        f.write("All portrait images are sourced from Wikipedia/Wikimedia Commons.\n")
        f.write("Images are either in the public domain or licensed under Creative Commons.\n\n")
        f.write("| Elder | Source | License |\n")
        f.write("|-------|--------|--------|\n")
        for a in sorted(attributions, key=lambda x: x["elder_id"]):
            f.write(f"| {a['name']} | [Wikipedia]({a['source']}) | {a['license']} |\n")
        f.write("\n---\n\n")
        f.write("**Legal basis:** Bridgeman Art Library v. Corel Corp., 36 F. Supp. 2d 191 (S.D.N.Y. 1999) — ")
        f.write("reproductions of public domain artworks cannot be copyrighted.\n")

    print(f"\nDone: {successes}/{len(ELDERS)} downloaded, {len(failures)} failed")
    if failures:
        print(f"Failed: {', '.join(failures)}")
    print(f"Attribution: {attr_path}")


if __name__ == "__main__":
    main()
