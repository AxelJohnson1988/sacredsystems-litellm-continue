"""SacredSystems local model gateway.

This package routes inference. It is not a state authority.
Proposals, commits, and receipts belong to Warden in
phx-os-architecture-repo. Gateway outputs are model tokens only.
"""

from .router import GatewayRouter, RouteDecision, InferenceResult

__all__ = ["GatewayRouter", "RouteDecision", "InferenceResult"]
