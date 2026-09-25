"""Almacenamiento local seguro para los shares de una party."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID


class LocalStorage:
    """Guarda shares bajo nombres derivados exclusivamente de UUID validados."""

    def __init__(self, directory: str | Path) -> None:
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, video_id: UUID, payload: bytes) -> Path:
        if not isinstance(video_id, UUID):
            raise ValueError("video_id debe ser un UUID válido.")
        if not payload:
            raise ValueError("El contenido del share no puede estar vacío.")

        destination = self._directory / f"{video_id}.share"
        temporary_path: Path | None = None

        try:
            with NamedTemporaryFile(
                mode="wb",
                dir=self._directory,
                prefix=f".{video_id}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(payload)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, destination)
        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise

        return destination
