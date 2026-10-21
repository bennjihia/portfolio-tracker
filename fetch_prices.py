#!/usr/bin/env python3
"""Fetch NSE Kenya prices from the TradingView screener and write prices.json.

Runs server-side (GitHub Actions), so browser CORS limits don't apply.
Leaves prices.json untouched if the fetch fails or looks wrong.
"""
import datetime
import json
import os
import sys
import urllib.request

URL = "https://scanner.tradingview.com/kenya/scan"
OUT = "prices.json"
ALIAS = {"NSE": "NSEL"}  # TradingView ticker -> tracker ticker
MIN_TICKERS = 20

body = {
    "filter": [],
    "columns": ["name", "close", "change"],
    "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
    "range": [0, 200],
}
req = urllib.request.Request(
    URL,
    data=json.dumps(body).encode(),
    headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://www.tradingview.com",
        "Referer": "https://www.tradingview.com/",
    },
)

try:
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
except Exception as e:
    sys.exit(f"TradingView fetch failed: {e}")

prices = {}
for row in data.get("data", []):
    sym = (row.get("s") or "").split(":")[-1]
    sym = ALIAS.get(sym, sym)
    d = row.get("d") or []
    try:
        p = float(d[1])
        c = float(d[2]) if d[2] is not None else 0.0
    except (IndexError, TypeError, ValueError):
        continue
    if sym and p > 0:
        prices[sym] = {"p": round(p, 4), "c": round(c, 2)}

if len(prices) < MIN_TICKERS:
    sys.exit(f"Only {len(prices)} tickers returned; keeping existing {OUT}")

old = {}
if os.path.exists(OUT):
    try:
        with open(OUT, encoding="utf-8") as f:
            old = json.load(f).get("prices", {})
    except Exception:
        pass

if old == prices:
    print("No price changes; leaving file as is")
    sys.exit(0)

out = {
    "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source": "TradingView (NSEKE)",
    "prices": dict(sorted(prices.items())),
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)
print(f"Wrote {len(prices)} prices")
