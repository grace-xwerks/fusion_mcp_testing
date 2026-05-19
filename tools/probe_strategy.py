"""Run CAM-15 against a single strategy name via the live Fusion MCP.

Usage:
    py tools/probe_strategy.py <strategy_name>           # one strategy
    py tools/probe_strategy.py s1 s2 s3 ...              # several, sequential

Writes each result to docs/strategy_params/<name>.txt.
"""
import json, sys, pathlib, urllib.request, urllib.error

URL = "http://localhost:27182/mcp"


def post(payload, sid=None):
    h = {"Content-Type": "application/json",
         "Accept": "application/json, text/event-stream"}
    if sid: h["MCP-Session-Id"] = sid
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                 headers=h, method="POST")
    r = urllib.request.urlopen(req, timeout=120)
    return r.headers, r.read().decode("utf-8")


def session():
    h, _ = post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                 "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                            "clientInfo": {"name": "probe", "version": "0"}}})
    sid = h.get("MCP-Session-Id")
    post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, sid)
    return sid


CAM15_TEMPLATE = '''
import adsk.core, adsk.cam

STRATEGY = {strategy!r}

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first.")
        return
    strat_obj = adsk.cam.OperationStrategy.createFromString(STRATEGY)
    if not strat_obj:
        print(f"Unknown strategy: {{STRATEGY!r}}"); return
    op_type = (adsk.cam.OperationTypes.TurningOperation
               if strat_obj.isTurningStrategy
               else adsk.cam.OperationTypes.MillingOperation)
    seed = next((b for b in cam.designRootOccurrence.bRepBodies), None)
    if seed is None:
        print("No bRepBody"); return
    si = cam.setups.createInput(op_type); si.models = [seed]
    setup = cam.setups.add(si)
    try:
        oi = setup.operations.createInput(STRATEGY)
        ps = oi.parameters
        print(f"strategy={{STRATEGY}}  count={{ps.count}}")
        print(f"  title={{strat_obj.title}}")
        for i in range(ps.count):
            p = ps.item(i)
            v = getattr(p, "value", None)
            print(f"  - {{p.name:32s}}  expr={{getattr(p,'expression','')!r}}  valueType={{type(v).__name__ if v else ''}}  title={{getattr(p,'title','')!r}}")
    finally:
        setup.deleteMe()
'''


def main():
    out_dir = pathlib.Path("docs/strategy_params")
    out_dir.mkdir(parents=True, exist_ok=True)
    sid = session()
    for s in sys.argv[1:]:
        src = CAM15_TEMPLATE.format(strategy=s)
        _, body = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": "fusion_mcp_execute",
                                   "arguments": {"featureType": "script",
                                                 "object": {"script": src}}}}, sid)
        d = json.loads(body)
        try:
            txt = d["result"]["content"][0]["text"]
        except (KeyError, IndexError):
            txt = body
        out_path = out_dir / f"{s}.txt"
        out_path.write_text(txt, encoding="utf-8")
        print(f"{s:20s} -> {out_path}  ({len(txt)} chars)")


if __name__ == "__main__":
    main()
