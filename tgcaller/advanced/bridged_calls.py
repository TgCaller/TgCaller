"""Bridged-call capability boundary.

TgCaller currently has no decoded-audio receive path that can mix or forward
media between independent Telegram group calls. This manager therefore fails
closed instead of joining calls and reporting a non-functional bridge as live.
"""

import logging
from typing import Dict, List, Optional, Set

from ..types import AudioConfig

logger = logging.getLogger(__name__)


class BridgedCallManager:
    """Public placeholder that explicitly reports unsupported bridging."""

    def __init__(self, caller):
        self.caller = caller
        self.bridges: Dict[str, Set[int]] = {}
        self.logger = logger

    async def create_bridge(
        self,
        bridge_name: str,
        chat_ids: List[int],
        audio_config: Optional[AudioConfig] = None,
    ) -> bool:
        """Return False until bidirectional audio forwarding is implemented."""
        if not isinstance(bridge_name, str) or not bridge_name.strip():
            raise ValueError("bridge_name must be a non-empty string")
        if len(chat_ids) < 2 or len(set(chat_ids)) != len(chat_ids):
            raise ValueError("At least two distinct chat IDs are required")
        self.logger.warning(
            "Bridged calls are not supported: TgCaller has no inter-call "
            "decoded-audio forwarding transport yet"
        )
        return False

    async def destroy_bridge(self, bridge_name: str) -> bool:
        """No bridges can be active while media forwarding is unsupported."""
        return self.bridges.pop(bridge_name, None) is not None

    async def add_chat_to_bridge(self, bridge_name: str, chat_id: int) -> bool:
        return False

    async def remove_chat_from_bridge(self, bridge_name: str, chat_id: int) -> bool:
        return False

    def get_bridge_info(self, bridge_name: str):
        return None

    def list_bridges(self) -> List[str]:
        return list(self.bridges)
