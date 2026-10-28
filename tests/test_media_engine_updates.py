"""Tests for Telegram group-call connection update parsing and mode selection."""

from types import SimpleNamespace

import pytest

from tgcaller.mtproto.media_engine import (
    classify_group_call_connection_params,
    extract_group_call_connection_params,
    extract_webrtc_transport_description,
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



def _valid_transport_response():
    return {
        "ufrag": "ignored-local-value",
        "pwd": "ignored-local-password",
        "fingerprints": [{"hash": "sha-256", "fingerprint": "AA:BB", "setup": "passive"}],
        "transport": {
            "ufrag": "remote-ufrag",
            "pwd": "remote-password",
            "fingerprints": [
                {"hash": "sha-256", "fingerprint": "CC:DD", "setup": "active"}
            ],
            "candidates": [
                {
                    "port": "3478",
                    "protocol": "udp",
                    "network": "1",
                    "generation": "0",
                    "id": "candidate-1",
                    "component": "1",
                    "foundation": "foundation-1",
                    "priority": "12345",
                    "ip": "192.0.2.10",
                    "type": "relay",
                    "rel-addr": "10.0.0.1",
                    "rel-port": "5000",
                }
            ],
        },
    }


def test_extracts_nested_telegram_webrtc_transport_description():
    parsed = extract_webrtc_transport_description(_valid_transport_response())

    assert parsed["ufrag"] == "remote-ufrag"
    assert parsed["pwd"] == "remote-password"
    assert parsed["fingerprints"] == [
        {"hash": "sha-256", "fingerprint": "CC:DD", "setup": "active"}
    ]
    assert parsed["candidates"][0]["ip"] == "192.0.2.10"
    assert parsed["candidates"][0]["rel-addr"] == "10.0.0.1"


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda p: p.update({"stream": True}), "stream/RTMP mode"),
        (lambda p: p.pop("transport"), "transport object"),
        (lambda p: p["transport"].pop("candidates"), "candidates list"),
        (lambda p: p["transport"].update({"candidates": []}), "at least one ICE candidate"),
        (lambda p: p["transport"].update({"ufrag": ""}), "non-empty ufrag"),
        (
            lambda p: p["transport"]["candidates"][0].pop("foundation"),
            "ICE candidate at index 0 is invalid",
        ),
        (
            lambda p: p["transport"]["candidates"][0].update({"port": "65536"}),
            "out-of-range port",
        ),
        (
            lambda p: p["transport"]["candidates"][0].update({"priority": "not-a-number"}),
            "invalid priority",
        ),
        (
            lambda p: p["transport"]["candidates"][0].update({"protocol": "sctp"}),
            "unsupported protocol",
        ),
        (
            lambda p: p["transport"]["candidates"][0].update({"type": "unknown"}),
            "unsupported type",
        ),
        (
            lambda p: p["transport"]["fingerprints"][0].update({"setup": "actpass"}),
            "unsupported setup",
        ),
        (
            lambda p: p["transport"]["fingerprints"][0].update({"hash": "md5"}),
            "unsupported hash",
        ),
    ],
)
def test_rejects_invalid_webrtc_transport_response(mutate, message):
    params = _valid_transport_response()
    mutate(params)

    with pytest.raises(ValueError, match=message):
        extract_webrtc_transport_description(params)
