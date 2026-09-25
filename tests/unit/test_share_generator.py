"""Pruebas de propiedades del prototipo de Secret Sharing XOR de T09."""

import numpy as np
import pytest

from client.sharing import ShareGenerationError, XorShareGenerator


def _pattern(size: int) -> bytes:
    """Crea datos deterministas que ejercitan todos los valores de un byte."""

    block = bytes(range(256))
    return (block * ((size + len(block) - 1) // len(block)))[:size]


def _reconstruct(shares: tuple[bytes, bytes, bytes]) -> bytes:
    arrays = [np.frombuffer(share, dtype=np.uint8) for share in shares]
    return np.bitwise_xor(np.bitwise_xor(arrays[0], arrays[1]), arrays[2]).tobytes()


@pytest.mark.parametrize("size", [1, 10, 1024, 64 * 1024, 1024 * 1024])
def test_generates_exactly_three_full_length_reconstructable_shares(size: int) -> None:
    payload = _pattern(size)

    shares = XorShareGenerator().generate(payload)

    assert isinstance(shares, tuple)
    assert len(shares) == 3
    assert all(isinstance(share, bytes) for share in shares)
    assert [len(share) for share in shares] == [size, size, size]
    assert _reconstruct(shares) == payload


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(bytes(4096), id="zeros"),
        pytest.param(bytes([0xFF]) * 4096, id="ff"),
        pytest.param(_pattern(8193), id="mixed"),
    ],
)
def test_reconstructs_payloads_with_representative_byte_patterns(payload: bytes) -> None:
    shares = XorShareGenerator(chunk_size=257).generate(payload)

    assert _reconstruct(shares) == payload
    assert all(len(share) == len(payload) for share in shares)


def test_generation_is_randomized_and_no_individual_share_is_the_payload() -> None:
    # A non-trivial payload makes accidental equality cryptographically negligible.
    payload = _pattern(64 * 1024)
    generator = XorShareGenerator(chunk_size=1024)

    first = generator.generate(payload)
    second = generator.generate(payload)

    assert all(left != right for left, right in zip(first, second))
    assert all(share != payload for share in first)
    assert all(share != payload for share in second)
    assert _reconstruct(first) == payload
    assert _reconstruct(second) == payload


def test_chunk_boundaries_do_not_change_the_secret() -> None:
    payload = _pattern(1025)

    shares = XorShareGenerator(chunk_size=16).generate(payload)

    assert _reconstruct(shares) == payload


def test_rejects_empty_payload() -> None:
    with pytest.raises(ShareGenerationError, match="payload secreto no puede estar vac"):
        XorShareGenerator().generate(b"")


@pytest.mark.parametrize("chunk_size", [0, -1, -1024])
def test_rejects_non_positive_chunk_size(chunk_size: int) -> None:
    with pytest.raises(ValueError, match="chunk_size debe ser positivo"):
        XorShareGenerator(chunk_size=chunk_size)
