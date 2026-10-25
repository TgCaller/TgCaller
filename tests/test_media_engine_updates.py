"""Tests for Telegram group-call connection update parsing."""

from types import SimpleNamespace

import pytest

from tgcaller.mtproto.media_engine import extract_group_call_connection_params


class UpdateGroupCallConnection:
    def __init__(self, data):
        self.params = SimpleNamespace(data=data)


class UpdateOther:
    pass


def test_extracts_webrtc_connection_params_from_updates_collection():
    updates = SimpleNamespace(
        updates=[
            UpdateOther(),
            UpdateGroupCallConnection(
                '{"ufrag":"server-ice","pwd":"secret","fingerprints":[]}'
            ),
        ]
    )

    assert extract_group_call_connection_params(updates) == {
        "ufrag": "server-ice",
        "pwd": "secret",
        "fingerprints": [],
    }


@pytest.mark.parametrize(
    "data, expected",
    [
        ('{"stream":true}', {"stream": True}),
        ('{"stream":true,"rtmp":true}', {"stream": True, "rtmp": True}),
    ],
)
def test_preserves_stream_mode_response_for_engine_dispatch(data, expected):
    update = UpdateGroupCallConnection(data)

    assert extract_group_call_connection_params(update) == expected


@pytest.mark.parametrize(
    "data",
    ["", "not-json", "[]", "null", '"text"'],
)
def test_rejects_malformed_or_non_object_connection_params(data):
    with pytest.raises(ValueError):
        extract_group_call_connection_params(UpdateGroupCallConnection(data))


def test_rejects_updates_without_connection_parameters():
    with pytest.raises(ValueError, match="no UpdateGroupCallConnection"):
        extract_group_call_connection_params(SimpleNamespace(updates=[UpdateOther()]))


def test_rejects_connection_update_without_data_json():
    update = SimpleNamespace()
    update.__class__.__name__ = "UpdateGroupCallConnection"

    with pytest.raises(ValueError, match="no JSON params"):
        extract_group_call_connection_params(update)
