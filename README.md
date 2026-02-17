# d3p-protocol
Agent-to-agent service protocol on Lightning Network
# d3p — Agent-to-Agent Service Protocol on Lightning Network

**10 live services. Machine-readable. Composable. Pay per call in satoshis.**

d3p is an open protocol that enables autonomous AI agents to discover, evaluate, compose, and pay for services from other agents — no human in the loop, sub-cent settlement, in milliseconds.

## Live Right Now

```bash
# Protocol entry point — any agent starts here
curl https://digital3.ai/.well-known/d3p-manifest.json

# Full service directory — 10 machine-readable services
curl https://labs.digital3.ai/api/services/manifest

# Single service descriptor
curl https://labs.digital3.ai/api/services/search/manifest

# Check if two services can chain together
curl -X POST https://labs.digital3.ai/api/services/check-compatibility \
  -H "Content-Type: application/json" \
  -d '{"source_service": "search", "target_service": "vibe-check"}'

# Find all valid service pipelines
curl "https://labs.digital3.ai/api/services/pipelines?input_type=text&output_type=structured_data"

# Discover services by capability and price
curl -X POST https://labs.digital3.ai/api/discover/query \
  -H "Content-Type: application/json" \
  -d '{"capability": "text", "max_price_sats": 50, "status": "active"}'
```

These are not mocks. These are live endpoints returning real data from real services.

## What d3p Solves

Google AP2, Stripe ACP, and Mastercard Agent Pay all solve the same problem: **how does a human authorize an agent to spend money?**

d3p solves a different problem: **how do agents discover, evaluate, compose, and pay OTHER AGENTS autonomously?**

AP2 stops at the agent. d3p starts there.

| Feature | Google AP2 | Stripe ACP | x402 | d3p |
|---|---|---|---|---|
| Agent→Agent payments | ❌ | ❌ | ⚠️ Basic | ✅ Lightning |
| Service discovery | ❌ | ❌ | ❌ | ✅ |
| Schema composability | ❌ | ❌ | ❌ | ✅ |
| Cryptographic reputation | ❌ | ❌ | ❌ | ✅ |
| Sub-cent micropayments | ❌ Card minimums | ❌ | ⚠️ | ✅ |
| Instant settlement | ❌ 2-day | ❌ | ⚠️ | ✅ Milliseconds |
| Pipeline orchestration | ❌ | ❌ | ❌ | ✅ |
| No human required | ❌ Mandates | ❌ | ✅ | ✅ |

## How It Works

### 1. Discover
An agent fetches `/.well-known/d3p-manifest.json` from any d3p node. This returns the protocol entry point with endpoints for service discovery, registration, and health.

### 2. Query
The agent queries the discovery endpoint with filters — capability, max price in sats, minimum reputation, latency requirements. Gets back ranked results with full service descriptors.

### 3. Evaluate
Each service descriptor includes JSON Schema definitions for inputs and outputs, pricing in satoshis, latency profiles, composability tags, and Lightning node identity. The agent evaluates programmatically — no UI needed.

### 4. Compose
The compatibility checker tells agents whether Service A's output can feed into Service B's input, with automatic field mapping. The pipeline builder finds all valid multi-service chains ranked by cost and latency.

### 5. Pay
L402 protocol over Lightning Network. Agent requests service → receives Lightning invoice → pays (10-100 sats) → service executes → response returned. Sub-second. Final. No chargebacks.

### 6. Verify
Every transaction generates a cryptographic performance receipt. Reputation scores are computed from real transaction data — success rates, latency consistency, schema compliance. Trust from proof, not reviews.

## Protocol Stack

| Layer | What It Does | Status |
|---|---|---|
| Service Descriptors | JSON-LD machine-readable capability descriptors | ✅ Live |
| Schema Enforcement | Runtime validation of all inputs/outputs | ✅ Live |
| Discovery Protocol | Queryable service search by capability, price, reputation | ✅ Live |
| Performance Receipts | Cryptographic proof from every transaction | ✅ Live |
| Dynamic Pricing | Real-time price discovery based on demand and reputation | 🔨 Building |
| Streaming Payments | HODL invoice streaming for long-running tasks | 🔨 Building |
| Pipeline Orchestration | Multi-service workflow execution with atomic payments | 🔨 Building |
| SDK | `pip install d3p-sdk` for any developer to join | 🔨 Building |

## Live Services

10 services currently on the network, all with enforced schemas and machine-readable descriptors:

- **AI Web Search** — DuckDuckGo-powered search
- **Bitcoin Price Oracle** — Real-time BTC price data
- **Weather API** — Current weather conditions
- **Vibe Check** — Sentiment analysis
- **Error Translator** — Technical error explanation
- **And 5 more** — query the manifest for the full list

## Payment

- **Protocol:** L402 (HTTP 402 Payment Required)
- **Network:** Bitcoin Lightning Network
- **Range:** 10-100 satoshis per call
- **Settlement:** Instant, final, no chargebacks
- **Gateway:** autonom rails (bits-toll.com)

## The AP2 Bridge

d3p complements Google AP2. The integration story:

1. Human authorizes spending via AP2 (card rails, cryptographic mandates)
2. Agent enters d3p network
3. Agent discovers and calls 15 services autonomously
4. Each service paid via Lightning micropayment
5. Result returned to human

AP2 authorizes the purchase. d3p powers the fulfillment.

## Quick Start

```bash
# See what's available
curl https://digital3.ai/.well-known/d3p-manifest.json

# Browse all services
curl https://labs.digital3.ai/api/services/manifest

# Check if search output can feed into sentiment analysis
curl -X POST https://labs.digital3.ai/api/services/check-compatibility \
  -H "Content-Type: application/json" \
  -d '{"source_service": "search", "target_service": "vibe-check"}'
```

SDK coming soon: `pip install d3p-sdk`

## Built By

[digital3.ai](https://digital3.ai) — Austin, Bitcoin since 2015. $20/month infrastructure.

## License

MIT
