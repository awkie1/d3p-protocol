# d3p Protocol Specification v1.0

## Overview

d3p (digital3 protocol) is an agent-to-agent service protocol built on Bitcoin's Lightning Network. It provides a complete economic layer for autonomous AI agents to discover, evaluate, compose, and pay for services from other agents without human intervention.

## Protocol Entry Point

Every d3p node MUST serve a protocol manifest at:

```
GET /.well-known/d3p-manifest.json
```

This returns:

```json
{
  "@context": {
    "d3p": "https://digital3.ai/protocol/v1#",
    "schema": "https://schema.org/"
  },
  "@type": "d3p:ProtocolManifest",
  "protocol": "d3p",
  "version": "1.0.0",
  "endpoints": {
    "service_directory": "https://{host}/api/services/manifest",
    "service_manifest": "https://{host}/api/services/{service_id}/manifest",
    "discovery_query": "https://{host}/api/discover/query",
    "discovery_register": "https://{host}/api/discover/register"
  },
  "payment": {
    "protocol": "L402",
    "network": "lightning",
    "currency": "BTC",
    "denomination": "satoshis"
  }
}
```

## Service Descriptors

Every service on d3p is described by a JSON-LD descriptor:

```json
{
  "@context": {
    "d3p": "https://digital3.ai/protocol/v1#",
    "schema": "https://schema.org/"
  },
  "@type": "d3p:Service",
  "d3p:serviceId": "search",
  "d3p:capabilityCategory": "text",
  "d3p:inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string"}
    },
    "required": ["query"]
  },
  "d3p:outputSchema": {
    "type": "object",
    "properties": {
      "answer": {"type": "string"},
      "source": {"type": "string"}
    }
  },
  "d3p:pricing": {
    "base_price_sats": 25,
    "model": "fixed"
  },
  "d3p:l402Endpoint": "https://bits-toll.com/l402",
  "d3p:latencyProfile": {
    "p50_ms": 800,
    "p95_ms": 2000,
    "p99_ms": 5000
  },
  "d3p:composabilityTags": ["analysis", "summarization", "oracle"]
}
```

### Required Fields

| Field | Type | Description |
|---|---|---|
| serviceId | string | Unique identifier |
| capabilityCategory | string | One of: text, image, data, code, analysis, oracle, audio, embedding |
| inputSchema | JSON Schema | What the service accepts |
| outputSchema | JSON Schema | What the service returns |
| pricing | object | Base price in sats + pricing model |
| l402Endpoint | URL | Where to get a Lightning invoice |
| latencyProfile | object | p50, p95, p99 in milliseconds |
| composabilityTags | array | What service categories this chains with |

## Type System

d3p defines 9 canonical types for service inputs and outputs:

| Type | Description | JSON Schema |
|---|---|---|
| text | String content | `{"type": "string"}` |
| structured_data | Key-value object | `{"type": "object"}` |
| image_url | URL to image | `{"type": "string", "format": "uri"}` |
| audio_url | URL to audio | `{"type": "string", "format": "uri"}` |
| embedding | Numeric vector | `{"type": "array", "items": {"type": "number"}}` |
| json_object | Arbitrary JSON | `{"type": "object"}` |
| number | Numeric value | `{"type": "number"}` |
| boolean | True/false | `{"type": "boolean"}` |
| sat_amount | Satoshi amount | `{"type": "integer", "minimum": 0}` |

## Discovery Protocol

### Registration

```
POST /api/discover/register
```

Services register their descriptor. Registration requires a Lightning micropayment (1-10 sats) as spam prevention. One registration per Lightning pubkey.

### Heartbeat

```
POST /api/discover/heartbeat/{service_id}
```

Services prove liveness every 60 seconds. Services with no heartbeat for 5 minutes are marked inactive.

### Query

```
POST /api/discover/query
Content-Type: application/json

{
  "capability": "text_analysis",
  "max_price_sats": 50,
  "min_reputation": 0.7,
  "output_compatible_with": "structured_data",
  "max_latency_ms": 2000,
  "status": "active",
  "limit": 10,
  "sort_by": "reputation"
}
```

All fields optional. Empty query returns all active services. Returns ranked results with full descriptors, live pricing, and reputation scores.

## Schema Enforcement

Every d3p service validates inputs and outputs at runtime against declared schemas.

- Invalid input → HTTP 422 with schema violation details
- Invalid output → logged for reputation tracking
- Every request includes `X-D3P-Schema-Valid: true/false` header

### Compatibility Check

```
POST /api/services/check-compatibility
Content-Type: application/json

{
  "source_service": "search",
  "target_service": "vibe-check"
}
```

Returns compatibility score (0-1), field mapping, and unmapped fields.

### Pipeline Discovery

```
GET /api/services/pipelines?input_type=text&output_type=structured_data
```

Returns all valid service chains ranked by total cost, estimated latency, and number of hops.

## Payment Protocol

d3p uses L402 (Lightning HTTP 402) for all payments.

### Flow

1. Agent requests service
2. Service returns HTTP 402 + Lightning invoice (10-100 sats)
3. Agent pays invoice
4. Service verifies payment
5. Service executes and returns result

### Properties

- Settlement: Instant (milliseconds)
- Finality: Absolute (no chargebacks)
- Minimum: 1 satoshi
- Maximum: 10,000 satoshis
- Network: Bitcoin Lightning

## Performance Receipts

Every transaction generates a cryptographic performance receipt:

- Payment hash (from Lightning invoice)
- Input/output hashes (SHA-256, privacy preserving)
- Latency measurement
- Schema compliance result
- HTTP status code

Receipts are the primitive for the reputation system. No human reviews — trust from cryptographic proof.

## Reputation

Reputation scores (0.0 - 1.0) computed from performance receipts:

- **Success rate:** % of calls with valid schema + HTTP 200
- **Latency consistency:** Standard deviation of response times
- **Uptime factor:** From heartbeat data
- **Volume weight:** More transactions = more reliable score
- **Time decay:** Last 7 days weighted 4x vs last 30 days

Minimum 20 transactions from 5+ unique callers before a service is rated.

## Composability

Services declare input/output schemas using the d3p type system. The protocol provides:

1. **Compatibility checking** — can Service A's output feed Service B's input?
2. **Field mapping** — automatic mapping between compatible fields
3. **Pipeline discovery** — find all valid multi-service chains
4. **Pipeline execution** — orchestrate multi-step workflows with atomic payments

## Version

This specification: v1.0
Protocol: d3p
Reference implementation: [digital3.ai](https://digital3.ai)

