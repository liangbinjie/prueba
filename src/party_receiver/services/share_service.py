"""Orquesta la persistencia de shares y las confirmaciones de recepción."""

from typing import Literal, TypedDict
from uuid import UUID

import httpx

from party_receiver.storage.local_storage import LocalStorage


class ShareReceipt(TypedDict):
    video_id: str
    party_id: int
    status: Literal["RECEIVED"]


class ShareStorageError(RuntimeError):
    """Indica que el share no pudo persistirse de forma segura."""


class CoordinatorNotificationError(RuntimeError):
    """Indica que el share se guardó, pero su confirmación falló."""


class ShareService:
    """Procesa un share recibido por una única party."""

    def __init__(
        self,
        party_id: int,
        storage: LocalStorage,
        coordinator_url: str,
        notification_timeout: float = 10.0,
    ) -> None:
        if party_id not in (0, 1, 2):
            raise ValueError("party_id debe ser 0, 1 o 2.")

        self._party_id = party_id
        self._storage = storage
        self._coordinator_url = coordinator_url.rstrip("/")
        self._notification_timeout = notification_timeout

    async def receive(self, video_id: UUID, share: bytes) -> ShareReceipt:
        try:
            self._storage.save(video_id, share)
        except OSError as exc:
            raise ShareStorageError("No se pudo almacenar el share recibido.") from exc

        await self._notify_coordinator(video_id)
        return {
            "video_id": str(video_id),
            "party_id": self._party_id,
            "status": "RECEIVED",
        }

    async def _notify_coordinator(self, video_id: UUID) -> None:
        endpoint = (
            f"{self._coordinator_url}/api/v1/videos/{video_id}/confirmations"
        )
        metadata = {"party_id": self._party_id, "status": "RECEIVED"}

        try:
            async with httpx.AsyncClient(timeout=self._notification_timeout) as client:
                response = await client.post(endpoint, json=metadata)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            message = (
                "El share fue almacenado, pero el Coordinator rechazó la "
                f"confirmación (HTTP {exc.response.status_code}). "
                "Puede reenviar el mismo share para reintentarla."
            )
            raise CoordinatorNotificationError(message) from exc
        except httpx.RequestError as exc:
            message = (
                "El share fue almacenado, pero no se pudo contactar al Coordinator. "
                "Puede reenviar el mismo share para reintentar la confirmación."
            )
            raise CoordinatorNotificationError(message) from exc

