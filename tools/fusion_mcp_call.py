"""Tiny CLI to call the running Fusion Desktop MCP server over HTTP.

Usage:
    py tools/fusion_mcp_call.py exec   <script_path>
    py tools/fusion_mcp_call.py read   <queryType json>
    py tools/fusion_mcp_call.py tools

The Fusion MCP HTTP server listens on http://localhost:27182/mcp by default
(toggle in Fusion: Preferences -> General -> API -> Fusion MCP Server).
"""
import json, sys, urllib.request, pathlib

URL = "http://localhost:27182/mcp"


def _post(payload, sid=None):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if sid:
        headers["MCP-Session-Id"] = sid
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode("utf-8"),
        headers=headers, method="POST")
    resp = urllib.request.urlopen(req)
    return resp.headers, resp.read().decode("utf-8")


def session():
    h, body = _post({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "fusion-mcp-call", "version": "0.1"},
        },
    })
    sid = h.get("MCP-Session-Id")
    _post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, sid)
    return sid


def call_tool(name, args):
    sid = session()
    _, body = _post({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": name, "arguments": args},
    }, sid)
    return body


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd = sys.argv[1]
    if cmd == "tools":
        sid = session()
        _, body = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, sid)
        print(body)
    elif cmd == "exec":
        script_path = pathlib.Path(sys.argv[2])
        src = script_path.read_text(encoding="utf-8")
        body = call_tool("fusion_mcp_execute", {
            "featureType": "script",
            "object": {"script": src},
        })
        # stdout on Windows is cp1252; write raw bytes to avoid encoding errors.
        sys.stdout.buffer.write(body.encode("utf-8"))
    elif cmd == "read":
        args = json.loads(sys.argv[2])
        print(call_tool("fusion_mcp_read", args))
    else:
        print("Unknown command:", cmd)


if __name__ == "__main__":
    main()
