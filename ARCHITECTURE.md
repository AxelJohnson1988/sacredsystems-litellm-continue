# Local inference gateway

## Role

This repository is the **inference adapter** for SacredSystems / MUSE.

It sits below Warden and beside MUSE agents:

```
MUSE agents / Continue.dev / IDE
              |
              v
     LiteLLM gateway (:4000)
              |
     +--------+--------+
     v                 v
  Ollama (:11434)   vLLM (:8000)
```

Phoenix / Warden remain the only path that can authorize or commit canonical state.
A completed chat call is **not** a receipt.

## What this repo owns

- Route table by task class (`chat`, `code`, `embed`, `long_context`)
- Local-first fallback order
- Cloud opt-in via `SSA_ALLOW_CLOUD=1`
- Continue.dev config pointed at the proxy
- Compose file for Ollama + LiteLLM on Node-1

## What this repo does not own

- Canonical state
- GPAM / Merkle / Ed25519 receipts
- DNS / brand-audit evidence
- Org transfer / device enrollment
- Neo4j / Kuzu schema (that is Akashic Core on Node-1)

## MUSE connection

MUSE agents currently hard-code OpenAI/Anthropic in `langchain_integration/agents.py`.
The next MUSE change is to construct those LLMs against `http://127.0.0.1:4000/v1`
with models `ssa-chat` / `ssa-code`, not against vendor APIs.

Until that patch lands, this gateway can still be used from Continue.dev
and from the Python `GatewayRouter`.

## Node placement

- Node-0 MacBook: Continue.dev client + this repo as config
- Node-1 Dell Precision: Ollama / optional vLLM / LiteLLM process
- Node-2 iPad: control only; do not run the GPU stack
