"""Structural contract tests for injected Telegram media engines."""

from tgcaller.mtproto import TelegramMediaEngine


class CompleteMediaEngine:
    async def create_join_payload(self, chat_id, audio_config=None, video_config=None):
        return {}

    async def handle_join_updates(self, chat_id, updates):
        return None

    async def is_connected(self, chat_id):
        return False

    async def source_id(self, chat_id):
        return 1

    async def close(self, chat_id):
        return None

    async def play_stream(self, chat_id, stream):
        return False

    async def stop_stream(self, chat_id):
        return False

    async def send_frame(self, chat_id, frame_data, frame_type):
        return False

    async def get_participants(self, chat_id, call_info):
        return []


def test_complete_media_engine_implements_protocol():
    assert isinstance(CompleteMediaEngine(), TelegramMediaEngine)


def test_incomplete_media_engine_does_not_implement_protocol():
    class IncompleteMediaEngine:
        async def create_join_payload(self, chat_id, audio_config=None, video_config=None):
            return {}

    assert not isinstance(IncompleteMediaEngine(), TelegramMediaEngine)
