"""Detecta quando o conteúdo da tela do device mudou de fato.

O encoder do device reenvia frames mesmo com a tela parada (~4 fps medido),
então "chegou frame" não significa "a tela mudou". Compara uma miniatura em
cinza de cada frame com a do anterior e ignora o ruído de compressão.
"""

from __future__ import annotations

import av
import numpy as np

_THUMB_WIDTH = 72
_THUMB_HEIGHT = 128
# Diferença mínima (0-255) de algum pixel da miniatura pra contar como mudança.
# Frames repetidos ficam bem abaixo disso (diferença média medida <= 0,1).
_PIXEL_THRESHOLD = 24


class ScreenChangeDetector:
    def __init__(self) -> None:
        self._previous: np.ndarray | None = None

    def reset(self) -> None:
        self._previous = None

    def changed(self, frame: av.VideoFrame) -> bool:
        thumb = frame.reformat(
            width=_THUMB_WIDTH, height=_THUMB_HEIGHT, format="gray"
        ).to_ndarray().astype(np.int16)
        previous, self._previous = self._previous, thumb
        if previous is None:
            return True
        return bool((np.abs(thumb - previous) > _PIXEL_THRESHOLD).any())
