"""wagmi-near CLI: python -m agent.cli <token.near> [--network mainnet] [--demo] [--json]

Uses the tool-using risk agent (holder discovery + snapshot + market + score).
"""
import argparse
import json
import pathlib

from .analyzer import analyze, roast
from .risk_agent import run as run_agent

FIX = pathlib.Path(__file__).resolve().parent.parent / "fixtures"
# Placeholder: Evo's public .near account for prize payout (never keys). Fill before submission.
OWNER_ACCOUNT = "YOUR_ACCOUNT.near"


def main(argv=None):
    ap = argparse.ArgumentParser(description="NearSight — read-only rug-risk agent for NEAR")
    ap.add_argument("token", nargs="?", default="wrap.near")
    ap.add_argument("--network", default="mainnet", choices=["testnet", "mainnet"])
    ap.add_argument("--holders", default="", help="comma-separated; skips auto discovery when set")
    ap.add_argument("--limit", type=int, default=25, help="max holders to discover (1-50)")
    ap.add_argument("--demo", action="store_true", help="offline: run the bundled fixtures")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if a.demo:
        snaps = [json.loads(p.read_text()) for p in sorted(FIX.glob("*.json"))]
        items = []
        for s in snaps:
            mk = s.pop("market", None)
            r = analyze(s, mk)
            items.append({"report": r, "roast": roast(r), "token": s.get("token"), "fixture": True})
        if a.json:
            print(json.dumps(items, indent=2))
            return
        for it in items:
            r = it["report"]
            print(f"\n== {r['symbol']} ({r['token']}) score {r['score']}/100: {r['verdict']}")
            for f in r["flags"]:
                print(f"  [{f['points']:+}] {f['msg']}")
            print("  " + it["roast"])
        return

    explicit = [h for h in a.holders.split(",") if h] or None
    result = run_agent(a.token, network=a.network, holders=explicit, holder_limit=max(1, min(a.limit, 50)))
    if a.json:
        print(json.dumps(result, indent=2))
        return
    if result.get("error"):
        print(f"ERROR: {result['error']}")
        for s in result.get("steps") or []:
            print(f"  tool={s['tool']} ok={s['ok']} {s['detail']}")
        return
    r = result["report"]
    print(f"\n== {r['symbol']} ({r['token']}) score {r['score']}/100: {r['verdict']}")
    print(f"  holders: {result['holder_count']} via {result['holder_source']} on {result['network']}")
    for f in r["flags"]:
        print(f"  [{f['points']:+}] {f['msg']}")
    print("  " + result["roast"])
    print("\n-- agent explanation --")
    print(result["explanation"])
    print("\n-- tools used --")
    for s in result["steps"]:
        mark = "ok" if s["ok"] else "FAIL"
        print(f"  [{mark}] {s['tool']}: {s['detail']}")


if __name__ == "__main__":
    main()
