"""ViewModel da tela de Configurações: expõe e persiste preferências do usuário."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, QStandardPaths, QUrl, Signal, Slot

from scrcpy_ui.storage.settings_store import SettingsStore

_SCREENSHOT_DIR_KEY = "screenshot_dir"


def _default_screenshot_dir() -> str:
    pictures = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
    return str(Path(pictures) / "scrcpy-ui")


class SettingsViewModel(QObject):
    screenshotDirChanged = Signal(str)

    def __init__(self, store: SettingsStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._screenshot_dir = self._store.get(_SCREENSHOT_DIR_KEY, _default_screenshot_dir())

    @Property(str, notify=screenshotDirChanged)
    def screenshotDir(self) -> str:
        return self._screenshot_dir

    @Slot(QUrl)
    def setScreenshotDir(self, folder_url: QUrl) -> None:
        path = folder_url.toLocalFile()
        if not path or path == self._screenshot_dir:
            return
        self._screenshot_dir = path
        self._store.set(_SCREENSHOT_DIR_KEY, path)
        self.screenshotDirChanged.emit(path)
