from agent.risk_agent import run


class FakeRPC:
    def snapshot(self, token, holders=()):
        return {
            "token": token,
            "code_hash": "abc",
            "keys": [],
            "metadata": {"spec": "ft-1.0.0", "symbol": "FAKE", "icon": "x"},
            "total_supply": "1000",
            "balances": {h: "10" for h in holders} or {"a.near": "10"},
        }


def test_agent_records_tool_steps(monkeypatch):
    import agent.risk_agent as ra

    monkeypatch.setattr(
        ra,
        "discover_holders",
        lambda *a, **k: ([{"account_id": "a.near", "balance": "100"}, {"account_id": "b.near", "balance": "50"}], "fastnear"),
    )
    monkeypatch.setattr(ra.market_mod, "dexscreener", lambda token: {"liquidity_usd": 100000, "volume_24h": 1000})
    out = run("fake.near", network="mainnet", rpc=FakeRPC())
    assert "error" not in out
    assert out["report"]["symbol"] == "FAKE"
    assert "discover_holders" in out["tools_used"]
    assert "snapshot_token" in out["tools_used"]
    assert "score_risk" in out["tools_used"]
    assert out["explanation"]
    snap_step = next(s for s in out["steps"] if s["tool"] == "snapshot_token")
    assert snap_step["data"]["rpc_balance_fetches"] == 0
