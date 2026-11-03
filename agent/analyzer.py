"""Memecoin risk scoring, adapted from wagmi_tracker's wallet-scoring ideas
(concentration, early-holder dominance, liquidity) plus NEAR-specific checks
(full-access keys on the token contract = upgradable / rug-able)."""


def _flag(flags, pts, code, msg):
    flags.append({"code": code, "points": pts, "msg": msg})


def analyze(snap, market=None):
    flags = []
    keys = snap.get("keys", [])
    full = [k for k in keys if k.get("access_key", {}).get("permission") == "FullAccess"]
    if full:
        _flag(flags, 35, "FULL_ACCESS_KEY", f"{len(full)} full-access key(s): owner can redeploy the contract")
    else:
        _flag(flags, -10, "LOCKED", "No full-access keys: contract is locked")
    if snap.get("code_hash") == "11111111111111111111111111111111":
        _flag(flags, 50, "NO_CODE", "Account has no contract deployed")

    md = snap.get("metadata") or {}
    if md.get("spec") != "ft-1.0.0":
        _flag(flags, 10, "SPEC", f"Non-standard spec {md.get('spec')!r}")
    if not md.get("icon"):
        _flag(flags, 5, "NO_ICON", "No icon in metadata (low-effort launch)")

    supply = int(snap.get("total_supply") or 0)
    bals = sorted((int(v) for v in snap.get("balances", {}).values()), reverse=True)
    top = (bals[0] / supply) if supply and bals else 0
    top5 = (sum(bals[:5]) / supply) if supply and bals else 0
    if top > 0.5:
        _flag(flags, 30, "WHALE", f"Top holder owns {top:.0%} of supply")
    elif top > 0.2:
        _flag(flags, 15, "WHALE", f"Top holder owns {top:.0%} of supply")
    if top5 > 0.8:
        _flag(flags, 10, "CONCENTRATED", f"Top 5 sampled holders own {top5:.0%}")

    if market:
        liq = market.get("liquidity_usd") or 0
        if liq < 5_000:
            _flag(flags, 20, "THIN_LIQ", f"Liquidity only ${liq:,.0f}")
        vol = market.get("volume_24h") or 0
        if liq and vol / liq > 20:
            _flag(flags, 10, "WASH", "24h volume >20x liquidity (possible wash trading)")

    score = max(0, min(100, sum(f["points"] for f in flags)))
    verdict = "RUG RISK" if score >= 60 else "CAUTION" if score >= 30 else "LOOKS OK"
    return {"token": snap.get("token"), "symbol": md.get("symbol"), "score": score,
            "verdict": verdict, "top_holder_pct": round(top * 100, 1), "flags": flags}


def roast(report):
    """One-line meme verdict for the demo / X card."""
    s = report["score"]
    sym = report.get("symbol") or "this token"
    if s >= 60:
        return f"${sym}: NGMI. {report['flags'][0]['msg']}. Touch grass, not this chart."
    if s >= 30:
        return f"${sym}: maybe WAGMI, maybe not. Size small, ser."
    return f"${sym}: WAGMI vibes. Contract locked, holders spread. Still DYOR."
