"""Gera os ícones do app a partir de resources/icons/scrcpy-ui.svg.

    uv run python packaging/make_icons.py

Saídas em resources/icons/:
- scrcpy-ui.png (512 px)  -> ícone da janela (Qt) e do .desktop no Linux
- scrcpy-ui.ico            -> executável do Windows (16..256 px)
- scrcpy-ui.icns           -> .app do macOS (16..1024 px)

Renderiza o SVG com o QtSvg (já vem no PySide6) e grava .ico/.icns com o
Pillow (dependência do adbutils).
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ICONS = Path(__file__).resolve().parents[1] / "resources" / "icons"
SVG = ICONS / "scrcpy-ui.svg"


def render(size: int) -> Image.Image:
    renderer = QSvgRenderer(str(SVG))
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return Image.open(io.BytesIO(bytes(buffer.data()))).convert("RGBA")


def main() -> None:
    QGuiApplication(sys.argv)  # QPainter/QImage precisam de uma app Qt
    if not SVG.is_file():
        sys.exit(f"SVG não encontrado: {SVG}")

    render(512).save(ICONS / "scrcpy-ui.png")

    # Cada tamanho renderizado direto do SVG (melhor nitidez que redimensionar)
    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [render(s) for s in ico_sizes]
    images[-1].save(ICONS / "scrcpy-ui.ico", sizes=[(s, s) for s in ico_sizes],
                    append_images=images[:-1])

    icns_base = render(1024)
    icns_base.save(ICONS / "scrcpy-ui.icns",
                   append_images=[render(s) for s in (16, 32, 64, 128, 256, 512)])

    for name in ("scrcpy-ui.png", "scrcpy-ui.ico", "scrcpy-ui.icns"):
        print(f"{name}: {(ICONS / name).stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
