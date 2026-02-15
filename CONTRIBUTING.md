# Contributing to d3p

## Register a Service

The fastest way to contribute is to register your own AI service on the d3p network.

### Requirements

- A running HTTP endpoint that accepts JSON and returns JSON
- A Lightning wallet (for receiving micropayments)
- Defined input/output schemas using the d3p type system

### Process

1. Define your service descriptor following the [SPEC](SPEC.md)
2. Register via the discovery endpoint
3. Pass automated certification (10 test calls, schema validation, latency check)
4. Your service is live and discoverable

SDK coming soon: `pip install d3p-sdk`

## Protocol Development

### Suggest Changes

Open an issue describing:
- What you want to change
- Why it improves agent-to-agent interaction
- Any breaking changes to existing services

### Submit a PR

1. Fork this repo
2. Create a branch: `git checkout -b my-change`
3. Make your changes
4. Submit a pull request with a clear description

### Areas We Need Help

- Framework integrations (LangChain, CrewAI, AutoGen tool wrappers)
- Additional service implementations
- Protocol spec improvements
- Documentation and examples
- Testing and security review

## Code of Conduct

Build things. Ship things. Be direct. Don't waste people's time.

## License

MIT — do whatever you want with it.
