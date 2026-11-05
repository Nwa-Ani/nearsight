"""Tool-using memecoin risk agent (tracks: security + agents).

Tools the agent can call (read-only, no keys, no signing):
  1. discover_holders  - FastNEAR then NearBlocks (balances included when indexed)
  2. snapshot_token    - NEAR JSON-RPC account + NEP-141 views (fills missing balances)
  3. market_data       - DexScreener (mainnet only)
  4. score_risk        - analyzer + roast

It records every tool call so judges (and the UI) can see how the verdict was reached.
"""
from __future__ import annotations

from .near_rpc import NearRPC
from .analyzer import analyze, roast
from . import market as market_mod
from .holders import discover_holders


def _step(steps, tool, detail, ok=True, data=None):
    entry = {"tool": tool, "ok": ok, "detail": detail}
    if data is not None:
        entry["data"] = data
    steps.append(entry)
    return entry


def run(token, network="mainnet", holders=None, holder_limit=25, rpc=None):
    """Run the risk agent end-to-end. Returns a JSON-serializable dict."""
    steps = []
    tools_used = []

    # Tool 1: holder discovery (prefer indexer balances to avoid N RPC calls)
    holder_rows, source = discover_holders(
        token, network=network, limit=holder_limit, explicit=holders
    )
    tools_used.append("discover_holders")
    holder_ids = [r["account_id"] for r in holder_rows]
    indexed_balances = {
        r["account_id"]: r["balance"]
        for r in holder_rows
        if r.get("balance") is not None
    }
    _step(
        steps,
        "discover_holders",
        f"source={source}; count={len(holder_ids)}; indexed_balances={len(indexed_balances)}; limit={holder_limit}",
        ok=bool(holder_ids) or source == "explicit",
        data={
            "source": source,
            "holders": holder_ids[:10],
            "holder_count": len(holder_ids),
            "indexed_balance_count": len(indexed_balances),
        },
    )

    # Tool 2: on-chain snapshot — only RPC-fetch balances missing from the indexer
    client = rpc or NearRPC(network)
    need_rpc = [h for h in holder_ids if h not in indexed_balances]
    try:
        snap = client.snapshot(token, need_rpc)
        if indexed_balances:
            bals = dict(snap.get("balances") or {})
            bals.update(indexed_balances)
            snap["balances"] = bals
        tools_used.append("snapshot_token")
        _step(
            steps,
            "snapshot_token",
            f"code_hash={snap.get('code_hash')}; keys={len(snap.get('keys') or [])}; "
            f"balances_total={len(snap.get('balances') or {})}; rpc_balance_fetches={len(need_rpc)}",
            ok=True,
            data={
                "code_hash": snap.get("code_hash"),
                "key_count": len(snap.get("keys") or []),
                "has_metadata": bool(snap.get("metadata")),
                "total_supply": snap.get("total_supply"),
                "rpc_balance_fetches": len(need_rpc),
            },
        )
    except Exception as e:  # noqa: BLE001
        tools_used.append("snapshot_token")
        _step(steps, "snapshot_token", f"failed: {type(e).__name__}: {e}", ok=False)
        return {
            "token": token,
            "network": network,
            "error": str(e),
            "steps": steps,
            "tools_used": tools_used,
            "explanation": f"Could not read token {token!r} on {network}: {e}",
        }

    # Tool 3: market (mainnet only)
    mk = None
    if network == "mainnet":
        tools_used.append("market_data")
        try:
            mk = market_mod.dexscreener(token)
            if mk:
                _step(
                    steps,
                    "market_data",
                    f"liquidity_usd={mk.get('liquidity_usd')}; volume_24h={mk.get('volume_24h')}",
                    ok=True,
                    data=mk,
                )
            else:
                _step(steps, "market_data", "no NEAR pairs on DexScreener", ok=True, data=None)
        except Exception as e:  # noqa: BLE001
            _step(steps, "market_data", f"failed: {type(e).__name__}: {e}", ok=False)

    # Tool 4: score
    tools_used.append("score_risk")
    report = analyze(snap, mk)
    meme = roast(report)
    _step(
        steps,
        "score_risk",
        f"score={report['score']}/100 verdict={report['verdict']}",
        ok=True,
        data={"score": report["score"], "verdict": report["verdict"], "flag_count": len(report["flags"])},
    )

    explanation = _explain(report, source, len(holder_ids), network, mk)
    return {
        "token": token,
        "network": network,
        "holder_source": source,
        "holder_count": len(holder_ids),
        "report": report,
        "roast": meme,
        "market": mk,
        "steps": steps,
        "tools_used": tools_used,
        "explanation": explanation,
        "tracks": ["security", "agents"],
    }


def _explain(report, holder_source, holder_count, network, market):
    lines = [
        f"I scored {report.get('symbol') or report.get('token')} at {report['score']}/100 "
        f"({report['verdict']}) on {network}.",
        f"Holders came from {holder_source} ({holder_count} accounts sampled).",
    ]
    if market and market.get("liquidity_usd") is not None:
        lines.append(
            f"DexScreener liquidity about ${float(market['liquidity_usd']):,.0f} "
            f"with 24h volume {market.get('volume_24h')}."
        )
    elif network == "mainnet":
        lines.append("No usable DexScreener NEAR pair; market flags skipped or thin.")
    if report["flags"]:
        lines.append("Risk flags (points contribute to the score):")
        for f in report["flags"]:
            lines.append(f"  [{f['points']:+}] {f['code']}: {f['msg']}")
    else:
        lines.append("No risk flags fired.")
    lines.append(
        "This agent is read-only: it never asks for a wallet connection, private key, or signature."
    )
    return "\n".join(lines)
