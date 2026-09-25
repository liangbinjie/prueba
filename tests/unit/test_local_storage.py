"""Pruebas unitarias del almacenamiento local de shares."""

import os
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest

from party_receiver.storage import local_storage as storage_module
from party_receiver.storage.local_storage import LocalStorage


def test_save_creates_non_empty_share_with_exact_content(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path / "party-0")
    video_id = uuid4()
    payload = bytes(range(256))

    destination = storage.save(video_id, payload)

    assert destination == tmp_path / "party-0" / f"{video_id}.share"
    assert destination.read_bytes() == payload
    assert destination.stat().st_size == len(payload)
    assert list(destination.parent.iterdir()) == [destination]


def test_save_rejects_empty_payload_without_creating_a_file(tmp_path: Path) -> None:
    storage_directory = tmp_path / "party-0"
    storage = LocalStorage(storage_directory)

    with pytest.raises(ValueError, match="vacío"):
        storage.save(uuid4(), b"")

    assert list(storage_directory.iterdir()) == []


def test_save_atomically_overwrites_an_existing_share(tmp_path: Path) -> None:
    storage_directory = tmp_path / "party-0"
    storage = LocalStorage(storage_directory)
    video_id = uuid4()
    destination = storage.save(video_id, b"old-share")

    returned_path = storage.save(video_id, b"new-share")

    assert returned_path == destination
    assert destination.read_bytes() == b"new-share"
    assert [path.name for path in storage_directory.iterdir()] == [
        f"{video_id}.share"
    ]


def test_failed_atomic_replace_preserves_previous_share_and_removes_temp_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    storage_directory = tmp_path / "party-0"
    storage = LocalStorage(storage_directory)
    video_id = uuid4()
    destination = storage.save(video_id, b"known-good-share")

    def fail_replace(source: os.PathLike[str], target: os.PathLike[str]) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(storage_module.os, "replace", fail_replace)

    with pytest.raises(OSError, match="simulated replace failure"):
        storage.save(video_id, b"incomplete-new-share")

    assert destination.read_bytes() == b"known-good-share"
    assert [path.name for path in storage_directory.iterdir()] == [
        f"{video_id}.share"
    ]


def test_separate_party_directories_are_isolated(tmp_path: Path) -> None:
    video_id = uuid4()
    party_0_directory = tmp_path / "party-0"
    party_1_directory = tmp_path / "party-1"
    party_0 = LocalStorage(party_0_directory)
    party_1 = LocalStorage(party_1_directory)

    party_0.save(video_id, b"share-zero")
    party_1.save(video_id, b"share-one")

    assert (party_0_directory / f"{video_id}.share").read_bytes() == b"share-zero"
    assert (party_1_directory / f"{video_id}.share").read_bytes() == b"share-one"
    assert {path.parent for path in tmp_path.rglob("*.share")} == {
        party_0_directory,
        party_1_directory,
    }


@pytest.mark.parametrize(
    "malicious_id",
    ["../../escaped", "..\\..\\escaped", "/absolute/path", "not-a-uuid"],
)
def test_save_rejects_non_uuid_identifiers_and_prevents_path_traversal(
    tmp_path: Path, malicious_id: str
) -> None:
    storage_directory = tmp_path / "nested" / "party-0"
    storage = LocalStorage(storage_directory)

    with pytest.raises(ValueError, match="UUID"):
        storage.save(cast(UUID, malicious_id), b"secret")

    assert list(tmp_path.rglob("*.share")) == []
    assert list(storage_directory.iterdir()) == []
