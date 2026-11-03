# WAGMI Meme Agent (NEAR)

Built at NEAR HACKATHON 2026. A memecoin risk agent for NEAR NEP-141 tokens: it reads the token contract over
NEAR RPC and returns a 0-100 rug-risk score, the reasons, and a one-line meme verdict ("WAGMI" or "NGMI").

Tracks: Memecoins With Mechanics, AI Security & Defense (scam detection).

## What it checks
- Full-access keys on the token account (owner can redeploy = rug vector) vs. a locked contract
- Contract deployed at all, NEP-141 `ft-1.0.0` spec, metadata quality
- Holder concentration (`ft_balance_of` for sampled holders vs `ft_total_supply`), adapted from wagmi_tracker's wallet scoring
- Mainnet only: liquidity and wash-trading signals from DexScreener

Read-only. The agent never holds, asks for, or signs with private keys. Testnet by default.

## Run
```bash
python3 -m agent.cli --demo                                  # offline demo with fixtures
python3 -m agent.cli wrap.testnet                            # live testnet token
python3 -m agent.cli <token.near> --network mainnet --holders a.near,b.near
pip install pytest && python -m pytest -q
```
No dependencies beyond Python 3.9+ standard library.

## Prize account
`YOUR_ACCOUNT.near` (placeholder, set in `agent/cli.py`)

## License
All rights reserved. See LICENSE.
