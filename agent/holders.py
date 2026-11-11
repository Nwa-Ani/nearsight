"""Automatic NEP-141 top-holder discovery via public indexers.

Primary: FastNEAR GET /v1/ft/{token}/top (no key) — includes balances.
Fallback: NearBlocks GET /v1/fts/{token}/holders (no key for public rate).
Never holds keys; read-only HTTP.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

FASTNEAR = {
    "mainnet": "https://api.fastnear.com",
    "testnet": "https://test.api.fastnear.com",
}
NEARBLOCKS = {
    "mainnet": "https://api.nearblocks.io",
    "testnet": "https://api-testnet.nearblocks.io",
}
UA = {"User-Agent": "nearsight/1.0 (+https://github.com/Nwa-Ani/nearsight)"}


def _get_json(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def from_fastnear(token, network="mainnet", limit=25):
    base = FASTNEAR.get(network) or FASTNEAR["mainnet"]
    tid = urllib.parse.quote(token, safe="")
    data = _get_json(f"{base}/v1/ft/{tid}/top")
    accounts = data.get("accounts") or []
    rows = []
    for row in accounts:
        acct = row.get("account_id")
        bal = row.get("balance")
        if not acct:
            continue
        try:
            bal_i = int(bal or 0)
        except (TypeError, ValueError):
            bal_i = 0
        if bal_i <= 0:
            continue
        rows.append({"account_id": acct, "balance": str(bal_i)})
        if len(rows) >= limit:
            break
    return rows, "fastnear"


def from_nearblocks(token, network="mainnet", limit=25):
    base = NEARBLOCKS.get(network) or NEARBLOCKS["mainnet"]
    tid = urllib.parse.quote(token, safe="")
    rows = []
    page = 1
    while len(rows) < limit and page <= 3:
        data = _get_json(f"{base}/v1/fts/{tid}/holders?page={page}&per_page=25")
        holders = data.get("holders") or data.get("data") or []
        if not holders:
            break
        for row in holders:
            acct = row.get("account") or row.get("account_id") or row.get("owner_account_id")
            amount = row.get("amount") or row.get("balance") or row.get("quantity")
            if not acct:
                continue
            try:
                amt_i = int(amount or 0)
            except (TypeError, ValueError):
                amt_i = 0
            if amt_i <= 0:
                continue
            if any(r["account_id"] == acct for r in rows):
                continue
            rows.append({"account_id": acct, "balance": str(amt_i)})
            if len(rows) >= limit:
                break
        page += 1
    return rows, "nearblocks"


def discover_holders(token, network="mainnet", limit=25, explicit=None):
    """Return (rows[{account_id,balance}], source). Prefer explicit list when provided.

    Explicit holders have balance None so the RPC snapshot can fill them.
    """
    if explicit:
        cleaned = [h.strip() for h in explicit if h and h.strip()]
        if cleaned:
            return [{"account_id": h, "balance": None} for h in cleaned[:limit]], "explicit"
    errors = []
    for fn in (from_fastnear, from_nearblocks):
        try:
            rows, source = fn(token, network=network, limit=limit)
            if rows:
                return rows, source
            errors.append(f"{fn.__name__}: empty")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, RuntimeError) as e:
            errors.append(f"{fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{fn.__name__}: {type(e).__name__}: {e}")
    return [], "none:" + "; ".join(errors) if errors else "none"
