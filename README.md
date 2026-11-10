# NearSight

**NearSight** was built at **NEAR HACKATHON 2026**. A read-only memecoin **risk agent** for NEAR NEP-141 tokens.

It discovers top holders, reads the token contract over NEAR RPC, optionally pulls DexScreener liquidity, scores rug risk 0-100, and explains the verdict with every tool step recorded.

**Tracks:** `security` (AI Security & Defense / scam detection), `agents` (Agent Economy).

**Not financial advice.** Read-only. Never asks for a wallet connection, private key, or signature.

## Baseline vs hackathon work

| Tag / source | What it is |
| --- | --- |
| Tag `pre-hackathon` | Snapshot of the first MVP commit (CLI + fixtures + analyzer) before this security+agents build |
| This branch (`main` after hackathon commits) | Automatic holder discovery, tool-using risk agent, JSON API, free web UI, AI-screener README |
| https://wagmi-tracker.onrender.com | Prior Solana product (`wagmi_tracker`). Concentration / early-holder ideas were adapted here for NEAR NEP-141. Only the NEAR integration in this repo is judged. |

Diff hint: compare `pre-hackathon` to `hackathon-submission` (tag added at final submit) or to `main`.

## What the agent checks

- Full-access keys on the token account (owner can redeploy = rug vector) vs locked contract
- Contract deployed, NEP-141 `ft-1.0.0` spec, metadata quality
- Holder concentration via automatic discovery (FastNEAR top holders, NearBlocks fallback) plus live `ft_balance_of`
- Mainnet only: liquidity and wash-trading signals from DexScreener

## Tools the agent uses (in order)

1. `discover_holders` — FastNEAR `/v1/ft/{token}/top`, fallback NearBlocks `/v1/fts/{token}/holders`
2. `snapshot_token` — NEAR JSON-RPC `view_account`, `view_access_key_list`, `ft_metadata`, `ft_total_supply`, `ft_balance_of`
3. `market_data` — DexScreener (mainnet)
4. `score_risk` — analyzer + meme roast line

## Run locally

```bash
python3 -m agent.cli --demo
python3 -m agent.cli wrap.near --network mainnet
python3 -m agent.cli wrap.near --network mainnet --json
python3 -m agent.server   # then open http://127.0.0.1:8080
pip install -r requirements.txt && python -m pytest -q
```

No runtime dependencies beyond Python 3.9+ standard library.

## AI screener: do X, then see Y

### Offline demo (no network)

1. Do: `python3 -m agent.cli --demo`
2. See: two blocks, one `LOOKS OK` (score 0) for `$WAGMI`, one `RUG RISK` (score 100) for `$NGMI`, each with point flags and a roast line.

### JSON API health

1. Do: start `python3 -m agent.server`, then `curl -s http://127.0.0.1:8080/health`
2. See: `{"ok": true, "service": "wagmi-meme-agent-near"}`

### Offline API demo

1. Do: `curl -s http://127.0.0.1:8080/api/demo`
2. See: JSON with `"demo": true` and two `items`, each with `report.score` and `roast`.

### Live mainnet analyze (example: wrap.near)

1. Do: `curl -s "http://127.0.0.1:8080/api/analyze?token=wrap.near&network=mainnet"`
2. See: JSON with `tools_used` including `discover_holders`, `snapshot_token`, `market_data`, `score_risk`; `holder_source` of `fastnear` (or `nearblocks`); `report.score` integer 0-100; `explanation` prose; `roast` string. No wallet fields.

### Web UI

1. Do: open `/`, paste `usdt.tether-token.near`, click Analyze
2. See: verdict, roast, holder source, tool step list, raw JSON. Page text states there is no wallet connect.

### Example success response (shape)

```json
{
  "token": "wrap.near",
  "network": "mainnet",
  "holder_source": "fastnear",
  "holder_count": 25,
  "tools_used": ["discover_holders", "snapshot_token", "market_data", "score_risk"],
  "report": {
    "token": "wrap.near",
    "symbol": "wNEAR",
    "score": 0,
    "verdict": "LOOKS OK",
    "flags": [{"code": "LOCKED", "points": -10, "msg": "No full-access keys: contract is locked"}]
  },
  "roast": "wNEAR: WAGMI vibes. Contract locked, holders spread. Still DYOR.",
  "explanation": "I scored wNEAR at 0/100 (LOOKS OK) on mainnet.\n..."
}
```

### Example error response (unknown token)

1. Do: `curl -s "http://127.0.0.1:8080/api/analyze?token=this-token-does-not-exist.near&network=mainnet"`
2. See: HTTP 502 JSON with `"error"` string and `steps` showing which tool failed. Still no wallet prompt.

## Hosted demo

Hosted demo (free plan; may cold-start): https://nearsight.onrender.com

The earlier URL https://wagmi-meme-agent-near.onrender.com stays up as an alias.

The repository and Render service still use the earlier `wagmi-meme-agent-near` id. The product name is NearSight.

- UI: `/`
- Health: `/health`
- Analyze: `/api/analyze?token=wrap.near&network=mainnet`

## Prize account

`YOUR_ACCOUNT.near` (placeholder in `agent/cli.py`). Set to Evo's real mainnet account before submission. Never commit keys.

## License

All rights reserved. See LICENSE. Published for hackathon judging and viewing.
