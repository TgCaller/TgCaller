"""Multi-client registry for advanced call features."""

from __future__ import annotations

from typing import Any, Dict, Optional


class MultiClientManager:
    """Manage several client connections by name."""

    def __init__(self):
        self._clients: Dict[str, Any] = {}

    def register(self, name: str, client: Any) -> Any:
        self._clients[name] = client
        return client

    def get(self, name: str) -> Optional[Any]:
        return self._clients.get(name)

    def remove(self, name: str) -> Optional[Any]:
        return self._clients.pop(name, None)

    def all(self) -> Dict[str, Any]:
        return dict(self._clients)

    def clear(self) -> None:
        self._clients.clear()
