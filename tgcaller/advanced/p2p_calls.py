"""Minimal peer-to-peer call manager for advanced call scenarios."""

from __future__ import annotations

from typing import Dict, Optional


class P2PCallManager:
    """Track P2P call state between local identifiers."""

    def __init__(self):
        self.calls: Dict[str, Dict[str, object]] = {}

    def start_call(self, call_id: str, *, peer: str, metadata: Optional[dict] = None) -> dict:
        payload = {"peer": peer, "metadata": metadata or {}, "active": True}
        self.calls[call_id] = payload
        return payload

    def end_call(self, call_id: str) -> Optional[dict]:
        return self.calls.pop(call_id, None)

    def get_call(self, call_id: str) -> Optional[dict]:
        return self.calls.get(call_id)
