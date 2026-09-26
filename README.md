# sacredsystems-litellm-continue

Local-first inference gateway for MUSE and Continue.dev.

Models may answer. They may not commit. Warden remains the only state authority
(`AxelJohnson1988/phx-os-architecture-repo`).

## Quick start (Node-1)

```bash
cp .env.example .env
docker compose up -d
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```

Proxy: `http://127.0.0.1:4000/v1`  
Ollama: `http://127.0.0.1:11434/v1`

Point Continue.dev at `continue/config.yaml`.

## Python router

```python
from ssa_gateway import GatewayRouter

router = GatewayRouter(allow_cloud=False)
decision = router.decide("code")
# decision.backend_name == "ollama_code"
```

Cloud is off unless `SSA_ALLOW_CLOUD=1`.

## Tests

```bash
PYTHONPATH=src python -m unittest tests.test_router
```

## Provenance boundary

`InferenceResult.is_receipt` is always `False`. Do not treat gateway output
as a Phoenix receipt, GPAM leaf, or Mindprint commitment.
