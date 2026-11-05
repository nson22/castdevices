"""Mapeia posições do mouse no VideoOutput (espaço do item QML) para o espaço de
coordenadas do device, levando em conta o letterbox/pillarbox do `contentRect`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContentRect:
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0


class MouseMapper:
    def __init__(self, device_width: int, device_height: int):
        self.device_width = device_width
        self.device_height = device_height
        self.content_rect = ContentRect(0.0, 0.0, float(device_width), float(device_height))

    def set_device_size(self, device_width: int, device_height: int) -> None:
        """Nova sessão de vídeo (ex.: rotação). A área do vídeo na tela
        (content_rect) é atualizada à parte, pelo QML."""
        self.device_width = device_width
        self.device_height = device_height

    def set_content_rect(self, x: float, y: float, width: float, height: float) -> None:
        self.content_rect = ContentRect(x, y, width, height)

    def map_point(self, item_x: float, item_y: float) -> tuple[int, int] | None:
        rect = self.content_rect
        if rect.width <= 0 or rect.height <= 0:
            return None
        rel_x = (item_x - rect.x) / rect.width
        rel_y = (item_y - rect.y) / rect.height
        rel_x = min(max(rel_x, 0.0), 1.0)
        rel_y = min(max(rel_y, 0.0), 1.0)
        dev_x = min(int(rel_x * self.device_width), self.device_width - 1)
        dev_y = min(int(rel_y * self.device_height), self.device_height - 1)
        return dev_x, dev_y

    @staticmethod
    def qt_buttons_to_android(qt_buttons: int) -> int:
        # Qt.MouseButton.LeftButton/RightButton/MiddleButton = 1/2/4, mesmos bits
        # de MotionEvent.BUTTON_PRIMARY/SECONDARY/TERTIARY no Android.
        return qt_buttons & 0b111
