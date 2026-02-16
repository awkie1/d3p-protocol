"""
d3p CrewAI Tool — call any d3p service from a CrewAI agent.

Usage:
    from d3p_crewai_tool import D3PServiceTool, discover_d3p_tools

    # Auto-discover all services, get one tool per service
    tools = discover_d3p_tools()

    # Or create a single tool
    tool = D3PServiceTool(service_id="btc-price")

    # Use with CrewAI
    from crewai import Agent, Task, Crew

    researcher = Agent(
        role="Market Analyst",
        goal="Analyze Bitcoin market conditions",
        tools=tools,
        llm="gpt-4",
    )

    task = Task(
        description="Get the current Bitcoin price and analyze market sentiment",
        agent=researcher,
        expected_output="Market report with price and sentiment",
    )

    crew = Crew(agents=[researcher], tasks=[task])
    result = crew.kickoff()

Requires: pip install crewai requests
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

MANIFEST_URL = "https://labs.digital3.ai/api/services/manifest"
BASE_URL = "https://labs.digital3.ai"


def _fetch_manifest(url: str = MANIFEST_URL) -> List[dict]:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()["services"]


class D3PServiceInput(BaseModel):
    """Input schema for a d3p service call."""
    payload: str = Field(description="JSON string with the service input parameters")


class D3PServiceTool(BaseTool):
    """CrewAI tool that calls a d3p protocol service via L402 Lightning."""

    name: str = ""
    description: str = ""
    args_schema: Type[BaseModel] = D3PServiceInput
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


def discover_d3p_tools(url: str = MANIFEST_URL, mock_payments: bool = True,
                       base_url: str = BASE_URL) -> List[D3PServiceTool]:
    """Discover all d3p services and return a CrewAI tool for each."""
    services = _fetch_manifest(url)
    return [
        D3PServiceTool(
            service_id=svc["service_id"],
            manifest_entry=svc,
            mock_payments=mock_payments,
            base_url=base_url,
        )
        for svc in services
    ]


if __name__ == "__main__":
    tools = discover_d3p_tools()
    print(f"Discovered {len(tools)} d3p tools:\n")
    for t in tools:
        print(f"  {t.name:30s} {t.pricing_sats:>3d} sats  {t.description[:60]}")
    print(f"\nTest call: btc-price")
    btc = next(t for t in tools if t.service_id == "btc-price")
    result = btc._run('{"currency": "usd"}')
    print(f"  Result: {result}")
