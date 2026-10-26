"""Tests for Telegram group-call connection update parsing and mode selection."""

from types import SimpleNamespace

import pytest

from tgcaller.mtproto.media_engine import (
    classify_group_call_connection_params,
    extract_group_call_connection_params,
)


class UpdateGroupCallConnection:
    def __init__(self, data, presentation=False):
        self.params = SimpleNamespace(data=data)
        self.presentation = presentation


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


def test_selects_main_connection_when_presentation_update_is_also_present():
    updates = [
        UpdateGroupCallConnection('{"ufrag":"presentation"}', presentation=True),
        UpdateGroupCallConnection('{"ufrag":"main"}'),
    ]

    assert extract_group_call_connection_params(updates) == {"ufrag": "main"}


def test_selects_presentation_connection_explicitly():
    updates = [
        UpdateGroupCallConnection('{"ufrag":"main"}'),
        UpdateGroupCallConnection('{"ufrag":"presentation"}', presentation=True),
    ]

    assert extract_group_call_connection_params(
        updates, presentation=True
    ) == {"ufrag": "presentation"}


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
    "params, expected",
    [
        ({"ufrag": "u", "pwd": "p"}, "webrtc"),
        ({"stream": False}, "webrtc"),
        ({"stream": True}, "stream"),
        ({"stream": True, "rtmp": False}, "stream"),
        ({"stream": True, "rtmp": True}, "rtmp"),
    ],
)
def test_classifies_telegram_connection_modes(params, expected):
    assert classify_group_call_connection_params(params) == expected


@pytest.mark.parametrize(
    "params",
    [
        None,
        [],
        {"stream": "true"},
        {"stream": True, "rtmp": "true"},
        {"rtmp": True},
    ],
)
def test_rejects_invalid_or_contradictory_connection_modes(params):
    with pytest.raises(ValueError):
        classify_group_call_connection_params(params)


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


def test_rejects_missing_requested_presentation_update():
    updates = [UpdateGroupCallConnection('{"ufrag":"main"}')]

    with pytest.raises(ValueError, match="for the presentation connection"):
        extract_group_call_connection_params(updates, presentation=True)


def test_rejects_connection_update_without_data_json():
    update_type = type("UpdateGroupCallConnection", (), {})
    with pytest.raises(ValueError, match="no JSON params"):
        extract_group_call_connection_params(update_type())
