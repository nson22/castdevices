"""Localização dos recursos (fontes, scrcpy-server.jar), rodando do código-fonte
ou de dentro do executável gerado pelo PyInstaller (sys._MEIPASS)."""

from __future__ import annotations

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    RESOURCES_DIR = Path(sys._MEIPASS) / "resources"
else:
    RESOURCES_DIR = Path(__file__).resolve().parents[2] / "resources"

QML_DIR = Path(__file__).resolve().parent / "qml"
FONTS_DIR = RESOURCES_DIR / "fonts"
SERVER_DIR = RESOURCES_DIR / "scrcpy-server"
