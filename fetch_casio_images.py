#!/usr/bin/env python3
"""
Fetch official Casio product photos for all CSV models.

Strategy:
  1. Parse casio.com US sitemap to find full variant URL per base model ID
  2. Query Wayback Machine CDX API for a genuine (pre-Akamai-block) snapshot URL
  3. Fetch archived HTML, extract og:image CDN URL
  4. Download image directly from casio.com CDN (/content/dam/ — no bot blocking)

Saves to images/originals/{model_id}.jpg
"""

import csv, os, re, time
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

SITEMAP_URLS = [
    "https://www.casio.com/us/sitemap.xml",        # US site
    "https://www.casio.com/intl/sitemap.xml",      # International site (catches MW-59, others)
    "https://www.casio.com/europe/sitemap.xml",    # European site (EU-exclusive models)
    "https://www.casio.com/jp/sitemap.xml"         # Japan site (early releases)
]
CDX_API     = "http://web.archive.org/cdx/search/cdx"
WBM_BASE    = "http://web.archive.org/web"
CSV_FILE    = "casio_watches_specs.csv"
OUTPUT_DIR  = "images/originals"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SESSION = requests.Session()
SESSION.headers["User-Agent"] = "Mozilla/5.0 (Linux; Android 13; Pixel 9) AppleWebKit/537.36"

# Add retry strategy for network timeouts
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
retry_strat = Retry(total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry_strat)
SESSION.mount("http://", adapter)
SESSION.mount("https://", adapter)

# CSV model codes that differ from casio.com slugs — map to correct prefix
MODEL_CODE_MAP = {
    "CA53W":    "CA-53W",
    "GWM-5610": "GW-M5610",
    "GWM-530A": "GW-M530A",
    "W-800":    "W-800H",
    "WS-210H":  "WS-2100H",
    "DW-5600E-1V": "DW-5600E",   # CSV duplicate of DW-5600E — treat as same
    "AW80":     "AW-80",         # US sitemap has AW-80-1AV, AW-80D-1AV; Wayback 2022-2023
    "AQ230":    "AQ-230",        # US sitemap has AQ-230A-2A2VT; Wayback 2023-2024
}

PREFERRED_SUFFIXES = ["-1V", "-1A1", "-1A", "-1", "-7A", "-1AV", "-1BV"]

def load_csv_models():
    with open(CSV_FILE, newline="") as f:
        return [r["Model"].strip() for r in csv.DictReader(f) if r["Model"].strip()]

def fetch_sitemap_urls():
    """Returns list of all product page URLs from all Casio sitemaps (US + INTL)."""
    all_urls = []
    for sitemap_url in SITEMAP_URLS:
        try:
            r = SESSION.get(sitemap_url, timeout=15)
            root = ET.fromstring(r.content)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            urls = [loc.text for loc in root.findall(".//sm:loc", ns)
                    if "/product." in loc.text]
            all_urls.extend(urls)
        except Exception as e:
            print(f"  Warning: failed to fetch {sitemap_url} — {e}")
    return all_urls

def find_variant_url(model_id, all_urls):
    """Find best variant URL for a base model ID using prefix matching."""
    lookup_id = MODEL_CODE_MAP.get(model_id, model_id)
    pattern = f"/product.{lookup_id}"
    candidates = [u for u in all_urls if pattern in u]
    if not candidates:
        return None
    # Exact match first (model already has full variant code)
    exact = [u for u in candidates if re.search(f"/product\\.{re.escape(lookup_id)}/$", u)]
    if exact:
        return exact[0]
    # Preferred suffix
    for suffix in PREFERRED_SUFFIXES:
        match = [u for u in candidates if f"/product.{lookup_id}{suffix}/" in u]
        if match:
            return match[0]
    return sorted(candidates)[0]

def get_wayback_snapshot(page_url):
    """
    Find a genuine pre-blocking snapshot of a casio.com product page.
    Targets 2019-2024 range when og:image was present and pages returned 200.
    """
    params = {
        "url": page_url,
        "output": "json",
        "fl": "timestamp,statuscode",
        "filter": "statuscode:200",
        "from": "20190101",
        "to": "20241228",
        "limit": 5,
        "fastLatest": "true",
    }
    try:
        r = SESSION.get(CDX_API, params=params, timeout=10)
        rows = r.json()
        if not rows or len(rows) < 2:  # rows[0] is header
            return None
        # Use the most recent genuine snapshot
        ts = rows[-1][0]
        return f"{WBM_BASE}/{ts}/{page_url}"
    except Exception as e:
        return None

def extract_og_image(archived_url):
    """Fetch archived HTML and extract og:image CDN URL."""
    try:
        r = SESSION.get(archived_url, timeout=12)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        og = soup.find("meta", property="og:image")
        if not og:
            return None
        img_url = og["content"]
        # Strip Wayback Machine prefix if present — get original casio.com CDN URL
        # WBM wraps images as: http://web.archive.org/web/{ts}im_/{original_url}
        m = re.search(r"web\.archive\.org/web/\d+im_/(.+)", img_url)
        if m:
            img_url = m.group(1)
            if not img_url.startswith("http"):
                img_url = "https://" + img_url
        return img_url
    except Exception as e:
        return None

def download_cdn_image(model_id, cdn_url):
    """Download image directly from casio.com CDN (no bot blocking on /content/dam/)."""
    out_path = os.path.join(OUTPUT_DIR, f"{model_id}.jpg")
    try:
        r = SESSION.get(cdn_url, timeout=15)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        print(f"    ✓ {len(r.content)//1024}KB saved")
        return True
    except Exception as e:
        print(f"    ✗ CDN fetch failed — {e}")
        return False

# --- Main ---
print("Loading sitemap...")
all_urls = fetch_sitemap_urls()
print(f"  Found {len(all_urls)} product URLs\n")

csv_models = load_csv_models()
missing = []

for model_id in csv_models:
    out_path = os.path.join(OUTPUT_DIR, f"{model_id}.jpg")
    if os.path.exists(out_path):
        print(f"  {model_id}: already downloaded")
        continue

    variant_url = find_variant_url(model_id, all_urls)
    if not variant_url:
        print(f"  {model_id}: not in sitemap")
        missing.append(model_id)
        continue

    print(f"  {model_id}: querying Wayback...", end="", flush=True)
    snapshot_url = get_wayback_snapshot(variant_url)
    if not snapshot_url:
        print(" no snapshot")
        missing.append(model_id)
        continue
    print(" found", flush=True)

    print(f"    → extracting og:image...", end="", flush=True)
    cdn_url = extract_og_image(snapshot_url)
    if not cdn_url:
        print(" not found")
        missing.append(model_id)
        continue
    print(" got URL", flush=True)

    download_cdn_image(model_id, cdn_url)
    time.sleep(0.5)

print(f"\nMissing ({len(missing)}): {', '.join(missing) if missing else 'none'}")
if missing:
    print(f"Use Pixabay supplement for these: python3 supplement_pixabay.py {' '.join(missing[:5])}")
