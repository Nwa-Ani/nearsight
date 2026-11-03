"""wagmi-near CLI: python -m agent.cli <token.near> [--holders a,b] [--network testnet] [--demo]"""
import argparse, json, pathlib
from .near_rpc import NearRPC
from .analyzer import analyze, roast
from . import market

FIX = pathlib.Path(__file__).resolve().parent.parent / "fixtures"
# Placeholder: Evo's public .near account (never keys). Fill in before submission.
OWNER_ACCOUNT = "YOUR_ACCOUNT.near"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("token", nargs="?", default="wrap.testnet")
    ap.add_argument("--network", default="testnet", choices=["testnet", "mainnet"])
    ap.add_argument("--holders", default="")
    ap.add_argument("--demo", action="store_true", help="offline: run the bundled fixtures")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.demo:
        snaps = [json.loads(p.read_text()) for p in sorted(FIX.glob("*.json"))]
        items = [(s, s.pop("market", None)) for s in snaps]
    else:
        snap = NearRPC(a.network).snapshot(a.token, [h for h in a.holders.split(",") if h])
        mk = None
        if a.network == "mainnet":
            try: mk = market.dexscreener(a.token)
            except Exception: mk = None
        items = [(snap, mk)]
    for snap, mk in items:
        r = analyze(snap, mk)
        if a.json:
            print(json.dumps(r, indent=2)); continue
        print(f"\n== {r['symbol']} ({r['token']}) score {r['score']}/100: {r['verdict']}")
        for f in r["flags"]:
            print(f"  [{f['points']:+}] {f['msg']}")
        print("  " + roast(r))


if __name__ == "__main__":
    main()
