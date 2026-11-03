"""Read-only NEAR JSON-RPC client. No keys, no signing."""
import base64, json, urllib.request

NETWORKS = {"testnet": "https://rpc.testnet.near.org", "mainnet": "https://rpc.mainnet.near.org"}
EMPTY_CODE = "11111111111111111111111111111111"


class NearRPC:
    def __init__(self, network="testnet", url=None, timeout=15):
        self.url = url or NETWORKS[network]
        self.timeout = timeout

    def _call(self, params):
        body = json.dumps({"jsonrpc": "2.0", "id": "wagmi", "method": "query", "params": params}).encode()
        req = urllib.request.Request(self.url, body, {"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            out = json.load(r)
        if "error" in out:
            raise RuntimeError(out["error"])
        res = out["result"]
        if "error" in res:
            raise RuntimeError(res["error"])
        return res

    def view_account(self, acct):
        return self._call({"request_type": "view_account", "finality": "final", "account_id": acct})

    def access_keys(self, acct):
        return self._call({"request_type": "view_access_key_list", "finality": "final", "account_id": acct})["keys"]

    def view(self, acct, method, args=None):
        a = base64.b64encode(json.dumps(args or {}).encode()).decode()
        res = self._call({"request_type": "call_function", "finality": "final", "account_id": acct,
                          "method_name": method, "args_base64": a})
        return json.loads(bytes(res["result"]).decode())

    def snapshot(self, token, holders=()):
        """Collect everything the analyzer needs for a NEP-141 token."""
        acct = self.view_account(token)
        snap = {"token": token, "code_hash": acct["code_hash"], "keys": self.access_keys(token)}
        snap["metadata"] = self.view(token, "ft_metadata")
        snap["total_supply"] = self.view(token, "ft_total_supply")
        snap["balances"] = {h: self.view(token, "ft_balance_of", {"account_id": h}) for h in holders}
        return snap
