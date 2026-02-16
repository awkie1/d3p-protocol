"""
d3p OpenAI Function Calling wrapper — expose d3p services as OpenAI tools.

Usage:
    from openai import OpenAI
    from d3p_openai_tool import D3POpenAI

    d3p = D3POpenAI()                          # discovers all 10 services
    tools = d3p.tool_definitions()              # OpenAI function schemas

    client = OpenAI()
    messages = [{"role": "user", "content": "What's the Bitcoin price?"}]
    resp = client.chat.completions.create(
        model="gpt-4", messages=messages, tools=tools,
    )

    # When the model calls a function, execute it:
    for call in resp.choices[0].message.tool_calls:
        result = d3p.execute(call.function.name, call.function.arguments)
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

Requires: pip install openai requests
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import requests

MANIFEST_URL = "https://labs.digital3.ai/api/services/manifest"
BASE_URL = "https://labs.digital3.ai"


def _fetch_manifest(url: str = MANIFEST_URL) -> List[dict]:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()["services"]


class D3POpenAI:
    """Discovers d3p services and exposes them as OpenAI function-calling tools."""

    def __init__(self, manifest_url: str = MANIFEST_URL, base_url: str = BASE_URL,
                 mock_payments: bool = True):
        self.base_url = base_url
        self.mock_payments = mock_payments
        self._services: Dict[str, dict] = {}
        for svc in _fetch_manifest(manifest_url):
            sid = svc["service_id"]
            endpoint = svc.get("endpoint", f"/api/services/{sid}")
            if not endpoint.startswith("http"):
                endpoint = f"{base_url}{endpoint}"
            self._services[f"d3p_{sid}"] = {**svc, "_endpoint": endpoint}

    def tool_definitions(self) -> List[dict]:
        """Return OpenAI-format tool definitions for all discovered services."""
        tools = []
        for func_name, svc in self._services.items():
            in_schema = svc.get("input_schema", {"type": "object", "properties": {}})
            params = {
                "type": "object",
                "properties": in_schema.get("properties", {}),
                "required": list(in_schema.get("properties", {}).keys()),
            }
            sats = svc.get("pricing", {}).get("sats", 0)
            cat = svc.get("capability_category", "")
            tools.append({
                "type": "function",
                "function": {
                    "name": func_name,
                    "description": f"{svc.get('description', '')} [{cat}, {sats} sats]",
                    "parameters": params,
                },
            })
        return tools

    def execute(self, function_name: str, arguments: str) -> str:
        """Execute a d3p service call. Pass the function name and JSON arguments string."""
        svc = self._services.get(function_name)
        if not svc:
            return json.dumps({"error": f"Unknown function: {function_name}"})

        try:
            data = json.loads(arguments) if isinstance(arguments, str) else arguments
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON arguments"})

        headers = {"Content-Type": "application/json"}
        if self.mock_payments:
            headers["X-D3P-Cert-Test"] = "true"

        resp = requests.post(svc["_endpoint"], json=data, headers=headers, timeout=15)

        if resp.status_code == 402 and not self.mock_payments:
            sats = svc.get("pricing", {}).get("sats", 0)
            return json.dumps({
                "error": "L402 payment required",
                "status": 402,
                "message": f"Service requires {sats} sats via Lightning",
            })

        try:
            return json.dumps(resp.json())
        except Exception:
            return resp.text[:500]

    def list_services(self) -> List[Dict[str, Any]]:
        """Return a summary of all discovered services."""
        return [
            {
                "function": name,
                "service_id": svc["service_id"],
                "name": svc.get("name", ""),
                "category": svc.get("capability_category", ""),
                "sats": svc.get("pricing", {}).get("sats", 0),
            }
            for name, svc in self._services.items()
        ]


if __name__ == "__main__":
    d3p = D3POpenAI()
    services = d3p.list_services()
    print(f"Discovered {len(services)} d3p functions:\n")
    for s in services:
        print(f"  {s['function']:30s} {s['sats']:>3d} sats  {s['name']}")
    print(f"\nTool definitions ({len(d3p.tool_definitions())} functions):")
    for t in d3p.tool_definitions():
        f = t["function"]
        params = list(f["parameters"]["properties"].keys())
        print(f"  {f['name']:30s} params: {params}")
    print(f"\nTest call: d3p_btc-price")
    result = d3p.execute("d3p_btc-price", '{"currency": "usd"}')
    print(f"  Result: {result}")
