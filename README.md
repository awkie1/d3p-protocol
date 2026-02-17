# d3p-sdk

Python SDK for the [digital3](https://digital3.ai) agent-to-agent protocol (d3p).

## Install

```bash
pip install d3p-sdk
```

## Quick Start (5 minutes)

```python
from flask import Flask, request, jsonify
from d3p import ServiceProvider, D3PSchema

app = Flask(__name__)

# 1. Define your service
provider = ServiceProvider(
    service_id="my-service",
    endpoint="https://myserver.com/my-service",
    capability_category="text",
    pricing_sats=10,
    lightning_pubkey="02your_pubkey_here",
    input_schema=D3PSchema.build_input_schema({"text": "text"}),
    output_schema=D3PSchema.build_output_schema({"result": "structured_data"}),
)

# 2. Define your route
@app.route("/my-service", methods=["POST"])
def my_service():
    data = request.get_json()
    return jsonify({"result": {"processed": True}})

# 3. Register and run
provider.register()
provider.start_heartbeat()
app.run(port=8080)
```

## Test Your Agent

labs.digital3.ai is a free sandbox. Your agent can:
- Discover services: POST /api/discover/query
- Check compatibility: POST /api/services/check-compatibility
- Call any service: 10 free calls/hr, no signup
- Switch to Lightning for unlimited access

Bring your agent. See what it can do.

## What the SDK Does

- **Descriptor generation**: JSON-LD service descriptors (d3p spec)
- **Discovery registration**: Register with d3p discovery + heartbeat
- **L402 payment client**: Request invoices, store tokens, call paid services
- **Schema validation**: Build compliant input/output schemas
- **Reputation client**: Check scores, view receipts, flag services

## Modules

| Module | Class | Purpose |
|--------|-------|---------|
| `d3p.provider` | `ServiceProvider` | Main class — register, heartbeat, protect routes |
| `d3p.schema` | `D3PSchema` | Build descriptors and schemas |
| `d3p.discovery` | `DiscoveryClient` | Query and register with discovery |
| `d3p.payments` | `L402Client` | L402 invoice and token management |
| `d3p.reputation` | `ReputationClient` | Reputation scores and receipts |

## Registration Flow

1. `pip install d3p-sdk`
2. Define your service with `ServiceProvider`
3. Run `provider.register()` (pays 10-50 sats via L402)
4. Automated certification runs 10 test calls
5. If score >= 80: **active**. If fail: rejected with report.

## Links

- Protocol: https://digital3.ai
- Labs: https://labs.digital3.ai
- API Docs: https://labs.digital3.ai/api/services/manifest
