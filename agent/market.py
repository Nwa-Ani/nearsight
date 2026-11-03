"""Optional mainnet market data from DexScreener (public, no key)."""
import json, urllib.request


def dexscreener(token):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "wagmi"}), timeout=15) as r:
        pairs = [p for p in (json.load(r).get("pairs") or []) if p.get("chainId") == "near"]
    if not pairs:
        return None
    p = max(pairs, key=lambda x: (x.get("liquidity") or {}).get("usd") or 0)
    return {"liquidity_usd": (p.get("liquidity") or {}).get("usd"),
            "volume_24h": (p.get("volume") or {}).get("h24"), "price_usd": p.get("priceUsd"), "url": p.get("url")}
