#!/usr/bin/env python3
"""
Family variant discovery: Generate and test common variant suffixes.
For successful model families, attempt to find variants with standard suffix patterns.
"""

import requests
import csv
import time
from urllib.parse import urlparse

# Common variant suffixes found in Casio model codes
SUFFIXES = [
    "-1A", "-1A1", "-1A2", "-1A3", "-1A5", "-1AV", "-1B", "-1B1", "-1B2", "-1C",
    "-2A", "-2A2VT", "-2E", "-2V",
    "-7B2", "-7D2",
    "-9V"
]

# Base families and their confirmed prefixes (from current successful models)
FAMILIES = {
    "GA": ["GA-100", "GA-110", "GA-700", "GA-2100", "GA-B2100"],
    "DW": ["DW-5600", "DW-6900", "DW-9052"],
    "AE": ["AE-1200"],
    "AQ": ["AQ-230"],
    "W": ["W-213", "W-215", "W-217", "W-218", "W-800"],
    "MW": ["MW-59", "MW-240", "MW-600"],
    "WV": ["WV-58", "WV-59"],
    "EFR": ["EFR-S108D"],
    "ECB": ["ECB-2000D"],
    "PRW": ["PRW-35"],
    "PRG": ["PRG-340"],
    "GBD": ["GBD-200"],
    "GST": ["GST-B400D"],
}

WAYBACK_CDX = "http://web.archive.org/cdx/search/cdx"

def test_variant_wayback(model_code):
    """Test if a model variant has a Wayback snapshot."""
    params = {
        "url": f"*casio.com*/{model_code}*",
        "matchType": "prefix",
        "output": "json",
        "filter": "statuscode:200",
        "sort": "timestamp:desc",
        "collapse": "urlkey",
        "showDupeCount": "on"
    }
    try:
        r = requests.get(WAYBACK_CDX, params=params, timeout=10)
        data = r.json()
        if len(data) > 1:  # [header, record, ...]
            return True
    except:
        pass
    return False

print("Family Variant Discovery")
print("=" * 50)

candidates = {}
tested = 0
found = 0

# For each base family
for prefix, bases in FAMILIES.items():
    for base in bases:
        # Extract base number (e.g., GA-100 → 100)
        base_num = base.split("-")[-1]

        for suffix in SUFFIXES:
            variant = f"{prefix}-{base_num}{suffix}"
            tested += 1

            if test_variant_wayback(variant):
                print(f"✓ {variant} found in Wayback")
                candidates[variant] = "Wayback"
                found += 1
                time.sleep(0.2)

            if tested % 20 == 0:
                print(f"  ... tested {tested} variants, {found} found")

print(f"\nTotal tested: {tested}")
print(f"New candidates found: {found}")
print(f"\nCandidates (verify before adding to CSV):")
for variant, source in sorted(candidates.items()):
    print(f"  {variant:<20} ({source})")

if found > 0:
    print(f"\nNext: Add {found} new models to casio_watches_specs.csv")
    print("Then run fetch_casio_images.py to retrieve images.")
