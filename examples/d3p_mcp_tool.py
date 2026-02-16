"""
d3p MCP Server — expose all d3p services as MCP tools.

Auto-discovers services from the d3p manifest and registers each as an
MCP tool that any MCP client (Claude Desktop, Cursor, etc.) can call.

Usage — stdio (Claude Desktop / claude-code):
    python3 d3p_mcp_tool.py

    Add to claude_desktop_config.json:
    {
      "mcpServers": {
        "d3p": {
          "command": "python3",
          "args": ["/root/d3p_mcp_tool.py"]
        }
      }
    }

Usage — SSE (remote):
    python3 d3p_mcp_tool.py --sse --port 8888

Env vars:
    D3P_MANIFEST_URL  — override manifest endpoint
    D3P_BASE_URL      — override base URL
    D3P_MOCK_PAYMENTS — "false" for live L402 Lightning payments (default: "true")

Requires: pip install mcp requests
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

import requests
from mcp.server.fastmcp import FastMCP

MANIFEST_URL = os.environ.get("D3P_MANIFEST_URL", "https://labs.digital3.ai/api/services/manifest")
BASE_URL = os.environ.get("D3P_BASE_URL", "https://labs.digital3.ai")
MOCK_PAYMENTS = os.environ.get("D3P_MOCK_PAYMENTS", "true").lower() != "false"


def _fetch_manifest(url: str = MANIFEST_URL) -> List[dict]:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()["services"]


def _call_service(endpoint: str, data: dict, sats: int) -> dict:
    """Execute a d3p service call with optional mock payment bypass."""
    headers = {"Content-Type": "application/json"}
    if MOCK_PAYMENTS:
        headers["X-D3P-Cert-Test"] = "true"

    resp = requests.post(endpoint, json=data, headers=headers, timeout=15)

    if resp.status_code == 402 and not MOCK_PAYMENTS:
        return {"error": "L402 payment required", "status": 402,
                "message": f"Service requires {sats} sats via Lightning"}
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text[:500], "status": resp.status_code}


# ── Build the MCP server ─────────────────────────────────────────────────────

mcp = FastMCP(
    "d3p",
    instructions=(
        "d3p protocol tools — call AI agent services on the digital3 network. "
        "Each tool maps to a live d3p service. Payments via L402 Lightning."
    ),
)

# Discover services and register each as an MCP tool
_services: Dict[str, dict] = {}

for _svc in _fetch_manifest():
    _sid = _svc["service_id"]
    _endpoint = _svc.get("endpoint", f"/api/services/{_sid}")
    if not _endpoint.startswith("http"):
        _endpoint = f"{BASE_URL}{_endpoint}"
    _svc["_endpoint"] = _endpoint
    _services[_sid] = _svc

    _sats = _svc.get("pricing", {}).get("sats", 0)
    _cat = _svc.get("capability_category", "")
    _desc = f"{_svc.get('description', '')} [{_cat}, {_sats} sats]"
    _props = _svc.get("input_schema", {}).get("properties", {})
    _param_doc = "; ".join(f"{k}: {v.get('description', v.get('type', ''))}"
                           for k, v in _props.items())

    # Build the tool function with closure over service data
    def _make_tool(sid: str, endpoint: str, sats: int, desc: str, param_doc: str):
        def tool_fn(params: str) -> str:
            """params: JSON string with the service input fields"""
            try:
                data = json.loads(params)
            except json.JSONDecodeError:
                return json.dumps({"error": "Invalid JSON"})
            return json.dumps(_call_service(endpoint, data, sats))

        tool_fn.__name__ = f"d3p_{sid}"
        tool_fn.__doc__ = f"{desc}. Input (JSON string): {param_doc or 'see docs'}"
        return tool_fn

    mcp.tool(name=f"d3p_{_sid}", description=_desc)(_make_tool(_sid, _endpoint, _sats, _desc, _param_doc))


@mcp.tool(name="d3p_list_services", description="List all available d3p services with pricing")
def list_services() -> str:
    """Returns a summary of all discovered d3p services."""
    summary = [
        {"service_id": s["service_id"], "name": s.get("name", ""),
         "category": s.get("capability_category", ""),
         "sats": s.get("pricing", {}).get("sats", 0),
         "description": s.get("description", "")}
        for s in _services.values()
    ]
    return json.dumps(summary, indent=2)


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--sse" in sys.argv:
        port = 8888
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        print(f"d3p MCP server (SSE) on port {port} — {len(_services)} tools")
        mcp.run(transport="sse")
    elif "--test" in sys.argv:
        print(f"d3p MCP server — {len(_services)} tools registered:\n")
        for sid, svc in _services.items():
            sats = svc.get("pricing", {}).get("sats", 0)
            print(f"  d3p_{sid:25s} {sats:>3d} sats  {svc.get('name', '')}")
        print(f"\nTest call: btc-price")
        result = _call_service(_services["btc-price"]["_endpoint"], {"currency": "usd"}, 5)
        print(f"  Result: {json.dumps(result)}")
        print(f"\nPayment mode: {'mock' if MOCK_PAYMENTS else 'live L402'}")
    else:
        mcp.run(transport="stdio")
