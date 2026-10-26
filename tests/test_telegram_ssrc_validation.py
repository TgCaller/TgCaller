"""Telegram SSRC validation follows the signed MTProto int32 representation."""

import pytest

from tgcaller.exceptions import ConnectionError
from tgcaller.mtproto.telegram_backend import (
    _validate_join_payload,
    _validate_source_id,
)


@pytest.mark.parametrize("ssrc", [-2147483648, -123456789, 1, 2147483647])
def test_accepts_nonzero_signed_int32_ssrc_values(ssrc):
    payload = {
        "ssrc": ssrc,
        "ufrag": "local-ufrag",
        "pwd": "local-password",
        "fingerprints": [
            {
                "hash": "sha-256",
                "fingerprint": "AA:BB",
                "setup": "passive",
            }
        ],
    }

    assert _validate_source_id(ssrc) == ssrc
    assert _validate_join_payload(payload)["ssrc"] == ssrc


@pytest.mark.parametrize("ssrc", [0, True, False, 2147483648, -2147483649, 1.5, "123"])
def test_rejects_invalid_source_id_values(ssrc):
    with pytest.raises(ConnectionError, match="non-zero integer source ID"):
        _validate_source_id(ssrc)


@pytest.mark.parametrize("ssrc", [0, True, False, 2147483648, -2147483649, 1.5, "123"])
def test_rejects_invalid_payload_ssrc_values(ssrc):
    payload = {
        "ssrc": ssrc,
        "ufrag": "local-ufrag",
        "pwd": "local-password",
        "fingerprints": [
            {
                "hash": "sha-256",
                "fingerprint": "AA:BB",
                "setup": "passive",
            }
        ],
    }

    with pytest.raises(ConnectionError, match="non-zero integer audio ssrc"):
        _validate_join_payload(payload)
