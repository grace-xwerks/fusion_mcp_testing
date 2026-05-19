"""Run a list of MCP_CAM_NN script folders sequentially via fusion_mcp_execute.

Usage: py tools/run_batch.py MCP_CAM_16... MCP_CAM_17... ...
"""
import json, sys, pathlib, urllib.request

URL = "http://localhost:27182/mcp"


def post(payload, sid=None):
    h = {"Content-Type": "application/json",
         "Accept": "application/json, text/event-stream"}
    if sid: h["MCP-Session-Id"] = sid
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                 headers=h, method="POST")
    return urllib.request.urlopen(req, timeout=180).read().decode()


def session():
    h = urllib.request.Request(URL,
        data=json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize",
                         "params":{"protocolVersion":"2024-11-05","capabilities":{},
                                   "clientInfo":{"name":"r","version":"0"}}}).encode(),
        headers={"Content-Type":"application/json",
                 "Accept":"application/json, text/event-stream"}, method="POST")
    r = urllib.request.urlopen(h, timeout=30)
    sid = r.headers.get("MCP-Session-Id")
    r.read()
    post({"jsonrpc":"2.0","method":"notifications/initialized","params":{}}, sid)
    return sid


def main():
    sid = session()
    root = pathlib.Path("FusionMCPTestLibrary")
    for folder in sys.argv[1:]:
        script_path = root / folder / f"{folder}.py"
        src = script_path.read_text(encoding="utf-8")
        body = post({"jsonrpc":"2.0","id":2,"method":"tools/call",
                     "params":{"name":"fusion_mcp_execute",
                               "arguments":{"featureType":"script",
                                            "object":{"script": src}}}}, sid)
        try:
            d = json.loads(body)
            txt = d["result"]["content"][0]["text"]
        except Exception:
            txt = body
        header = f"\n{'='*70}\n{folder}\n{'='*70}\n"
        sys.stdout.buffer.write(header.encode("utf-8"))
        sys.stdout.buffer.write(txt[:4000].encode("utf-8"))


if __name__ == "__main__":
    main()
