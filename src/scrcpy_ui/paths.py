"""Localização dos recursos (fontes, ícones, scrcpy-server.jar, adb), rodando
do código-fonte ou de dentro do executável gerado pelo PyInstaller
(sys._MEIPASS)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    RESOURCES_DIR = Path(sys._MEIPASS) / "resources"
else:
    RESOURCES_DIR = Path(__file__).resolve().parents[2] / "resources"

QML_DIR = Path(__file__).resolve().parent / "qml"
FONTS_DIR = RESOURCES_DIR / "fonts"
ICONS_DIR = RESOURCES_DIR / "icons"
SERVER_DIR = RESOURCES_DIR / "scrcpy-server"
# adb embutido no pacote de macOS/Linux (o adbutils só traz o do Windows).
# Colocado lá pelo workflow de release (platform-tools oficial do Google).
BUNDLED_ADB_DIR = RESOURCES_DIR / "platform-tools"


def use_bundled_adb() -> None:
    """Aponta o adbutils pro adb embutido, se houver e o usuário não tiver
    escolhido outro (ADBUTILS_ADB_PATH). Sem ele, o adbutils procura no PATH."""
    adb = BUNDLED_ADB_DIR / ("adb.exe" if sys.platform == "win32" else "adb")
    if not adb.is_file() or os.environ.get("ADBUTILS_ADB_PATH"):
        return
    if sys.platform != "win32" and not os.access(adb, os.X_OK):
        # Extração de zip/tar pode perder o bit de execução
        try:
            adb.chmod(adb.stat().st_mode | 0o111)
        except OSError:
            return
    os.environ["ADBUTILS_ADB_PATH"] = str(adb)
