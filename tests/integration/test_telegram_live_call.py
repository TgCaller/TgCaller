"""Opt-in end-to-end test against a real active Telegram group call.

Set TGCALLER_INTEGRATION=1, TG_API_ID, TG_API_HASH, TG_SESSION_STRING and
TG_CALL_CHAT_ID. The account must be able to join the already-active call.
This test sends silence, verifies outbound RTP byte counters, and checks the
server-side SSRC membership before leaving the call.
"""
import asyncio
import os

import pytest

from tgcaller.mtproto import PyrogramGroupCallBackend, resolve_active_group_call
from tgcaller.mtproto.engine.aiortc_engine import AiortcTelegramMediaEngine
from tgcaller.types import AudioConfig


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_real_telegram_group_call_join_rtp_and_server_membership():
    if os.getenv("TGCALLER_INTEGRATION") != "1":
        pytest.skip("Set TGCALLER_INTEGRATION=1 to run live Telegram integration")

    required = ("TG_API_ID", "TG_API_HASH", "TG_SESSION_STRING", "TG_CALL_CHAT_ID")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        pytest.skip("Missing live Telegram settings: " + ", ".join(missing))

    pyrogram = pytest.importorskip("pyrogram")
    chat_id = int(os.environ["TG_CALL_CHAT_ID"])
    client = pyrogram.Client(
        "tgcaller-live-integration",
        api_id=int(os.environ["TG_API_ID"]),
        api_hash=os.environ["TG_API_HASH"],
        session_string=os.environ["TG_SESSION_STRING"],
        in_memory=True,
    )
    engine = AiortcTelegramMediaEngine(connect_timeout=30, queue_size=10)
    backend = None
    started = False

    try:
        await client.start()
        started = True
        backend = PyrogramGroupCallBackend(
            client,
            resolve_call=lambda target: resolve_active_group_call(client, target),
            media_engine=engine,
        )

        assert await backend.connect_call(chat_id, AudioConfig()) is True
        assert await backend.is_healthy(chat_id) is True

        # Send paced 20 ms stereo s16le silence and require actual outbound RTP.
        silence = bytes(3840)
        deadline = asyncio.get_running_loop().time() + 10.0
        bytes_sent = 0
        while asyncio.get_running_loop().time() < deadline and bytes_sent == 0:
            await backend.send_frame(chat_id, silence, "audio")
            session = engine._sessions[chat_id]
            stats = await session.pc.getStats()
            bytes_sent = sum(
                report.bytesSent
                for report in stats.values()
                if getattr(report, "type", None) == "outbound-rtp"
                and getattr(report, "kind", None) == "audio"
                and hasattr(report, "bytesSent")
            )
            await asyncio.sleep(0.02)

        assert bytes_sent > 0, "aiortc did not report outbound audio RTP bytes"
        assert await backend.check_call(chat_id) is True

    finally:
        if backend is not None:
            try:
                await backend.disconnect_call(chat_id)
            except Exception:
                await engine.close(chat_id)
        else:
            await engine.close(chat_id)
        if started:
            await client.stop()
