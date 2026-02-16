"""
d3p LangChain Tool — call any d3p service from a LangChain agent.

Usage:
    from d3p_langchain_tool import D3PTool

    # Auto-discovers all services, creates one tool per service
    tools = D3PTool.from_manifest()

    # Or create a single tool for a specific service
    tool = D3PTool(service_id="btc-price")

    # Use with a LangChain agent
    from langchain.agents import initialize_agent, AgentType
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4")
    agent = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS)
    agent.run("What is the current Bitcoin price?")

Requires: pip install langchain requests
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Type

import requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

MANIFEST_URL = "https://labs.digital3.ai/api/services/manifest"
BASE_URL = "https://labs.digital3.ai"


def _fetch_manifest(url: str = MANIFEST_URL) -> List[dict]:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()["services"]


class D3PInput(BaseModel):
    """Input for a d3p service call — pass a JSON object."""
    payload: str = Field(description="JSON string of the service input")


class D3PTool(BaseTool):
    """LangChain tool that calls a d3p protocol service via L402 Lightning."""

    name: str = ""
    description: str = ""
    args_schema: Type[BaseModel] = D3PInput
    service_id: str = ""
    endpoint: str = ""
    pricing_sats: int = 0
    mock_payments: bool = True
    base_url: str = BASE_URL
    service_schema: Dict[str, Any] = {}

    def __init__(self, service_id: str = "", manifest_entry: Optional[dict] = None,
                 mock_payments: bool = True, base_url: str = BASE_URL, **kwargs):
        svc = manifest_entry or {}
        endpoint = svc.get("endpoint", f"/api/services/{service_id}")
        if endpoint.startswith("http"):
            full_url = endpoint
        else:
            full_url = f"{base_url}{endpoint}"

        svc_name = svc.get("name", service_id)
        svc_desc = svc.get("description", f"Call the {service_id} d3p service")
        category = svc.get("capability_category", "")
        sats = svc.get("pricing", {}).get("sats", 0)
        in_schema = svc.get("input_schema", {})
        props = in_schema.get("properties", {})
        fields = ", ".join(f'{k} ({v.get("type","")})' for k, v in props.items())

        super().__init__(
            name=f"d3p_{service_id}",
            description=(
                f"{svc_desc} [{category}, {sats} sats]. "
                f"Input fields: {fields or 'see docs'}. "
                f"Pass a JSON string as payload."
            ),
            service_id=service_id,
            endpoint=full_url,
            pricing_sats=sats,
            mock_payments=mock_payments,
            base_url=base_url,
            service_schema=in_schema,
            **kwargs,
        )

    def _run(self, payload: str) -> str:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON payload"})

        headers = {"Content-Type": "application/json"}
        if self.mock_payments:
            headers["X-D3P-Cert-Test"] = "true"

        resp = requests.post(self.endpoint, json=data, headers=headers, timeout=15)

        if resp.status_code == 402 and not self.mock_payments:
            return json.dumps({
                "error": "L402 payment required",
                "status": 402,
                "message": f"Service requires {self.pricing_sats} sats via Lightning",
            })

        try:
            return json.dumps(resp.json())
        except Exception:
            return resp.text[:500]

    async def _arun(self, payload: str) -> str:
        return self._run(payload)

    @classmethod
    def from_manifest(cls, url: str = MANIFEST_URL, mock_payments: bool = True,
                      base_url: str = BASE_URL) -> List["D3PTool"]:
        """Discover all d3p services and return a tool for each."""
        services = _fetch_manifest(url)
        return [
            cls(
                service_id=svc["service_id"],
                manifest_entry=svc,
                mock_payments=mock_payments,
                base_url=base_url,
            )
            for svc in services
        ]


if __name__ == "__main__":
    tools = D3PTool.from_manifest()
    print(f"Discovered {len(tools)} d3p tools:\n")
    for t in tools:
        print(f"  {t.name:30s} {t.pricing_sats:>3d} sats  {t.description[:60]}")
    print(f"\nTest call: btc-price")
    btc = next(t for t in tools if t.service_id == "btc-price")
    result = btc.run('{"currency": "usd"}')
    print(f"  Result: {result}")
