"""Generación reemplazable de shares sobre una representación binaria."""

from abc import ABC, abstractmethod
import secrets

import numpy as np


class ShareGenerationError(RuntimeError):
    """No fue posible crear los tres shares esperados."""


class ShareGenerator(ABC):
    """Contrato independiente del protocolo concreto de Secret Sharing."""

    @abstractmethod
    def generate(self, payload: bytes) -> tuple[bytes, bytes, bytes]:
        """Genera un share para cada una de las parties 0, 1 y 2."""


class XorShareGenerator(ShareGenerator):
    """PROTOTIPO T09: esquema XOR de tres shares, no compatible con MP-SPDZ."""

    def __init__(self, chunk_size: int = 1024 * 1024) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size debe ser positivo.")
        self._chunk_size = chunk_size

    def generate(self, payload: bytes) -> tuple[bytes, bytes, bytes]:
        if not payload:
            raise ShareGenerationError("El payload secreto no puede estar vacío.")

        size = len(payload)
        share_2 = bytearray(size)
        secret_view = memoryview(payload)

        try:
            # token_bytes ya devuelve bytes inmutables: conservarlos directamente
            # evita crear y luego copiar dos bytearrays completos al retornar.
            share_0 = secrets.token_bytes(size)
            share_1 = secrets.token_bytes(size)
            for offset in range(0, size, self._chunk_size):
                end = min(offset + self._chunk_size, size)
                chunk_length = end - offset

                secret_array = np.frombuffer(secret_view[offset:end], dtype=np.uint8)
                result = np.bitwise_xor(
                    secret_array,
                    np.frombuffer(
                        share_0,
                        dtype=np.uint8,
                        count=chunk_length,
                        offset=offset,
                    ),
                )
                np.bitwise_xor(
                    result,
                    np.frombuffer(
                        share_1,
                        dtype=np.uint8,
                        count=chunk_length,
                        offset=offset,
                    ),
                    out=result,
                )
                share_2[offset:end] = result.tobytes()
        except Exception as exc:
            raise ShareGenerationError("No se pudieron generar los shares XOR.") from exc
        finally:
            secret_view.release()

        return share_0, share_1, bytes(share_2)
