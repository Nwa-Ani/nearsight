import json
from pathlib import Path
from agent.analyzer import analyze, roast

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def test_safe_fixture_looks_ok():
    snap = json.loads((FIX / "01_safe.json").read_text())
    mk = snap.pop("market", None)
    r = analyze(snap, mk)
    assert r["score"] < 30
    assert r["verdict"] == "LOOKS OK"
    assert "WAGMI" in roast(r)


def test_rug_fixture_is_risky():
    snap = json.loads((FIX / "02_rug.json").read_text())
    mk = snap.pop("market", None)
    r = analyze(snap, mk)
    assert r["score"] >= 60
    assert r["verdict"] == "RUG RISK"
    assert "NGMI" in roast(r)


def test_full_access_key_adds_points():
    snap = {
        "token": "x.near",
        "code_hash": "abc",
        "keys": [{"access_key": {"permission": "FullAccess"}}],
        "metadata": {"spec": "ft-1.0.0", "symbol": "X", "icon": "i"},
        "total_supply": "100",
        "balances": {"a.near": "10"},
    }
    r = analyze(snap, None)
    codes = {f["code"] for f in r["flags"]}
    assert "FULL_ACCESS_KEY" in codes
