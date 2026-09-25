"""API para recibir el share correspondiente a una party."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from party_receiver.services.share_service import (
    CoordinatorNotificationError,
    ShareService,
    ShareStorageError,
)


router = APIRouter(prefix="/api/v1/shares", tags=["shares"])


class ShareReceipt(BaseModel):
    """Metadata devuelta después de recibir y confirmar un share."""

    video_id: UUID
    party_id: int
    status: Literal["RECEIVED"]


def get_share_service(request: Request) -> ShareService:
    return request.app.state.share_service


@router.post("/{video_id}", response_model=ShareReceipt)
async def receive_share(
    video_id: UUID,
    request: Request,
    service: Annotated[ShareService, Depends(get_share_service)],
) -> ShareReceipt:
    """Persiste bytes opacos y confirma su recepción al Coordinator."""

    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/octet-stream":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Content-Type debe ser application/octet-stream.",
        )

    share = await request.body()
    if not share:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El contenido del share no puede estar vacío.",
        )

    try:
        receipt = await service.receive(video_id, share)
    except ShareStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except CoordinatorNotificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return ShareReceipt(**receipt)

