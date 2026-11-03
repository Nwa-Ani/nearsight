import json, pathlib
from agent.analyzer import analyze, roast
from agent.cli import main
F = pathlib.Path(__file__).parent.parent / "fixtures"

def load(n):
    s = json.loads((F / n).read_text()); return s, s.pop("market")

def test_safe():
    r = analyze(*load("01_safe.json")); assert r["verdict"] == "LOOKS OK"

def test_rug():
    r = analyze(*load("02_rug.json"))
    assert r["verdict"] == "RUG RISK" and r["top_holder_pct"] == 80.0
    assert "NGMI" in roast(r)

def test_no_code():
    r = analyze({"code_hash": "11111111111111111111111111111111", "keys": [], "metadata": {}})
    assert any(f["code"] == "NO_CODE" for f in r["flags"])

def test_demo_cli(capsys):
    main(["--demo"]); assert "RUG RISK" in capsys.readouterr().out
