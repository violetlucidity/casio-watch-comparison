#!/usr/bin/env python3
"""
Fast family variant discovery: Sample key variant suffixes instead of exhaustive search.
Focus on most common patterns observed in successful Casio models.
"""

import requests
import time

# Most common suffixes from successful variants (observed in sitemaps)
COMMON_SUFFIXES = ["-1A", "-1A1", "-1B", "-2A", "-7B2"]

# Base families to test
FAMILIES = {
    "GA": 100,      # GA-100, GA-700, GA-2100
    "DW": 5600,     # DW-5600, DW-6900
    "W": 800,       # W-800, W-213
    "MW": 240,      # MW-240, MW-59
    "WV": 200,      # WV-200A, WV-59
    "PRG": 340,     # PRG-340
    "GBD": 200,     # GBD-200
}

WAYBACK_CDX = "http://web.archive.org/cdx/search/cdx"

def test_variant_wayback(model_code):
    """Check if variant exists in Wayback (with 5s timeout per request)."""
    params = {
        "url": f"*casio.com*product*{model_code}*",
        "matchType": "substring",
        "output": "json",
        "filter": "statuscode:200",
        "collapse": "urlkey",
        "showDupeCount": "on",
        "pageSize": 1  # Only need to know if ANY exists
    }
    try:
        r = requests.get(WAYBACK_CDX, params=params, timeout=5)
        data = r.json()
        return len(data) > 1  # header + at least 1 result
    except requests.Timeout:
        return False
    except:
        return False

print("Fast Family Variant Discovery")
print("=" * 50)

candidates = []
tested = 0
found = 0

for prefix, base_num in FAMILIES.items():
    for suffix in COMMON_SUFFIXES:
        variant = f"{prefix}-{base_num}{suffix}"
        tested += 1

        if test_variant_wayback(variant):
            print(f"✓ {variant}")
            candidates.append(variant)
            found += 1

        time.sleep(0.5)  # Respectful rate limit

print(f"\n{tested} variants tested, {found} new candidates found.")

if found > 0:
    print(f"\nNew models to verify:")
    for v in sorted(candidates):
        print(f"  {v}")
else:
    print("\nNo new variants discovered with common suffix patterns.")
