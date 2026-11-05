from agent.holders import discover_holders, from_fastnear


def test_explicit_holders_skip_indexer():
    rows, source = discover_holders("wrap.near", explicit=["a.near", "b.near"], limit=10)
    assert source == "explicit"
    assert [r["account_id"] for r in rows] == ["a.near", "b.near"]
    assert all(r["balance"] is None for r in rows)


def test_fastnear_wrap_near_live():
    rows, source = from_fastnear("wrap.near", network="mainnet", limit=5)
    assert source == "fastnear"
    assert len(rows) >= 1
    assert all(r["account_id"] and int(r["balance"]) > 0 for r in rows)
