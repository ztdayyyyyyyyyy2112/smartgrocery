"""Import freely licensed Wikimedia Commons photos for the demo catalog."""

import csv
import json
import sys
import re
from html import unescape
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "apps/web/public/products"
QUERIES = [
    "water spinach vegetable food", "red tomato vegetable", "banana fruit bunch", "red apple fruit",
    "milk carton 1 litre", "yogurt cups dairy", "cheese slices food", "pork belly meat",
    "raw chicken breast", "basa fish fillet", "chicken eggs carton", "sandwich bread loaf",
    "white rice grains", "instant noodles package", "instant pho noodles", "bottled drinking water",
    "cola soda can", "green tea bottle", "instant coffee jar", "beer cans six pack",
    "potato chips snack", "cookies biscuits tin", "fish sauce bottle", "cooking oil bottle",
    "white sugar bag", "dishwashing liquid bottle", "laundry detergent powder", "toilet paper rolls",
    "toothpaste tube", "shampoo bottle", "kimchi cabbage food", "fruit juice carton",
]
CURATED = {
    "SKU001": "File:Water Spinach.jpg",
    "SKU002": "File:Tomatoes plain and sliced.jpg",
    "SKU015": "File:Pho noodles in tomyam soup, Bangkok, 2017-11-12 (1).jpg",
    "SKU016": "File:Bottle of Water.jpg",
    "SKU019": "File:Instant Coffee In a Glass Jar.jpg",
    "SKU020": "File:Beer cans.jpg",
    "SKU022": "File:Box of cookies (7528010052).jpg",
    "SKU024": "File:Sunflower oil.jpg",
    "SKU027": "File:Laundry detergent 1.jpg",
    "SKU028": "File:Toilet paper roll.jpg",
    "SKU029": "File:Darlie Toothpaste Package.jpg",
    "SKU032": "File:Bolthouse Farms 100% Fruit Juice Smoothie, Blue Goodness (34041541536).jpg",
}


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "SmartGrocery academic demo (https://github.com/ztdayyyyyyyyyy2112/smartgrocery)"})
    with urlopen(req, timeout=35) as response:
        return response.read()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    DEST.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((ROOT / "database/demo/products.csv").open(encoding="utf-8")))
    credits = ["# Demo product photos", "", "Photos are illustrative and may differ from the exact SKU packaging. Source: Wikimedia Commons.", ""]
    for row, query in zip(rows, QUERIES, strict=True):
        sku = row["sku_id"]
        if sku in CURATED:
            params = {"action": "query", "titles": CURATED[sku], "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 640, "format": "json"}
        else:
            params = {"action": "query", "generator": "search", "gsrsearch": query + " filetype:bitmap", "gsrnamespace": 6,
                      "gsrlimit": 8, "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 640, "format": "json"}
        result = json.loads(fetch("https://commons.wikimedia.org/w/api.php?" + urlencode(params)))
        candidates = list(result.get("query", {}).get("pages", {}).values())
        chosen = None
        for page in candidates:
            info = page.get("imageinfo", [{}])[0]
            meta = info.get("extmetadata", {})
            license_name = meta.get("LicenseShortName", {}).get("value", "")
            if (info.get("thumburl") and info.get("width", 0) >= 500 and
                    page["title"].lower().endswith((".jpg", ".jpeg")) and
                    (license_name.startswith("CC") or "public domain" in license_name.lower())):
                chosen = (page, info, license_name)
                break
        if not chosen:
            print("NO PHOTO", sku, query)
            continue
        page, info, license_name = chosen
        target = DEST / f"{sku}.jpg"
        target.write_bytes(fetch(info["thumburl"]))
        meta = info.get("extmetadata", {})
        artist = unescape(re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "Wikimedia Commons contributor"))).strip()
        license_url = meta.get("LicenseUrl", {}).get("value", info["descriptionurl"])
        credits.append(f"- {sku}: [{page['title']}]({info['descriptionurl']}) — {artist} — [{license_name}]({license_url})")
        print(sku, target.stat().st_size, page["title"])
    (ROOT / "docs/product-photo-credits.md").write_text("\n".join(credits) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
