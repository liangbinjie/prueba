"""Abstracción y prototipo de Secret Sharing para T09."""

from client.sharing.share_generator import (
    ShareGenerationError,
    ShareGenerator,
    XorShareGenerator,
)


def create_share_generator() -> ShareGenerator:
    """Construye el generador configurado para la etapa actual del proyecto."""

    return XorShareGenerator()


__all__ = [
    "ShareGenerationError",
    "ShareGenerator",
    "XorShareGenerator",
    "create_share_generator",
]
