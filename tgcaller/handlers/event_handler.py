"""
Event Handler
"""

import logging
from typing import TYPE_CHECKING

from ..types import CallStatus, CallUpdate

if TYPE_CHECKING:
    from ..client import TgCaller

logger = logging.getLogger(__name__)


class EventHandler:
    """Bridge real PyTgCalls updates into TgCaller events."""

    def __init__(self, caller: "TgCaller"):
        self.caller = caller
        self._client = caller.client
        self._logger = logger
        self._backend_handler_registered = False

    async def setup(self):
        """Register a generic update handler when the backend supports it."""
        if self._backend_handler_registered:
            return

        backend = getattr(self.caller, "_calls_backend", None)
        on_update = getattr(backend, "on_update", None)
        if not callable(on_update):
            self._logger.debug("Call backend does not expose on_update")
            return

        try:
            decorator = on_update()
            decorator(self._handle_backend_update)
            self._backend_handler_registered = True
            self._logger.info("PyTgCalls update handler registered")
        except Exception:
            self._logger.exception("Failed to register PyTgCalls update handler")
            raise

    async def _handle_backend_update(self, _backend, update):
        """Translate backend stream-end and call-state updates to TgCaller events."""
        update_name = type(update).__name__
        chat_id = getattr(update, "chat_id", None)
        if chat_id is None:
            self._logger.debug("Ignoring backend update without chat_id: %s", update_name)
            return

        if update_name == "StreamEnded":
            session = self.caller._active_calls.get(chat_id)
            if session is not None:
                session.pop("current_stream", None)
                session["status"] = CallStatus.CONNECTED
            call_update = CallUpdate(
                chat_id=chat_id,
                status=CallStatus.CONNECTED if session is not None else CallStatus.ENDED,
                message="Media stream ended",
                metadata={"backend_update": update_name},
            )
            await self.caller._emit_event("stream_end", call_update)
            return

        if update_name == "ChatUpdate":
            status = str(getattr(update, "status", "")).lower()
            if "kicked" in status or "left" in status:
                self.caller._active_calls.pop(chat_id, None)
                call_update = CallUpdate(
                    chat_id=chat_id,
                    status=CallStatus.ENDED,
                    message=f"Telegram call state changed: {status}",
                    metadata={"backend_update": update_name},
                )
                await self.caller._emit_event("call_left", call_update)
                if "kicked" in status:
                    await self.caller._emit_event("kicked", call_update)
                return

        self._logger.debug("Unhandled backend update: %s", update_name)

    async def cleanup(self):
        """Reset local registration state during shutdown."""
        self._backend_handler_registered = False
        self._logger.info("Event handler cleanup complete")
