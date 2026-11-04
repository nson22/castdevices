"""ViewModel da tela de Configurações: expõe e persiste preferências do usuário."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, QStandardPaths, QUrl, Signal, Slot

from scrcpy_ui.storage.settings_store import SettingsStore

_SCREENSHOT_DIR_KEY = "screenshot_dir"
_STAY_AWAKE_KEY = "stay_awake"
_SHOW_TOUCHES_KEY = "show_touches"
_AUDIO_ENABLED_KEY = "audio_enabled"
_AUDIO_CODEC_KEY = "audio_codec"

AUDIO_CODECS = ("opus", "aac", "flac", "raw")


def _default_screenshot_dir() -> str:
    pictures = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
    return str(Path(pictures) / "scrcpy-ui")


class SettingsViewModel(QObject):
    screenshotDirChanged = Signal(str)
    stayAwakeChanged = Signal(bool)
    showTouchesChanged = Signal(bool)
    audioEnabledChanged = Signal(bool)
    audioCodecChanged = Signal(str)

    def __init__(self, store: SettingsStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._screenshot_dir = self._store.get(_SCREENSHOT_DIR_KEY, _default_screenshot_dir())
        self._stay_awake = self._store.get(_STAY_AWAKE_KEY, "0") == "1"
        self._show_touches = self._store.get(_SHOW_TOUCHES_KEY, "0") == "1"
        self._audio_enabled = self._store.get(_AUDIO_ENABLED_KEY, "1") == "1"
        self._audio_codec = self._store.get(_AUDIO_CODEC_KEY, "opus")
        if self._audio_codec not in AUDIO_CODECS:
            self._audio_codec = "opus"

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

    @Property(bool, notify=stayAwakeChanged)
    def stayAwake(self) -> bool:
        return self._stay_awake

    @stayAwake.setter
    def stayAwake(self, value: bool) -> None:
        if value == self._stay_awake:
            return
        self._stay_awake = value
        self._store.set(_STAY_AWAKE_KEY, "1" if value else "0")
        self.stayAwakeChanged.emit(value)

    @Property(bool, notify=showTouchesChanged)
    def showTouches(self) -> bool:
        return self._show_touches

    @showTouches.setter
    def showTouches(self, value: bool) -> None:
        if value == self._show_touches:
            return
        self._show_touches = value
        self._store.set(_SHOW_TOUCHES_KEY, "1" if value else "0")
        self.showTouchesChanged.emit(value)

    @Property(bool, notify=audioEnabledChanged)
    def audioEnabled(self) -> bool:
        return self._audio_enabled

    @audioEnabled.setter
    def audioEnabled(self, value: bool) -> None:
        if value == self._audio_enabled:
            return
        self._audio_enabled = value
        self._store.set(_AUDIO_ENABLED_KEY, "1" if value else "0")
        self.audioEnabledChanged.emit(value)

    @Property(str, notify=audioCodecChanged)
    def audioCodec(self) -> str:
        return self._audio_codec

    @audioCodec.setter
    def audioCodec(self, value: str) -> None:
        if value == self._audio_codec or value not in AUDIO_CODECS:
            return
        self._audio_codec = value
        self._store.set(_AUDIO_CODEC_KEY, value)
        self.audioCodecChanged.emit(value)
