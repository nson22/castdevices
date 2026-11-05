"""ViewModel da tela de Configurações: expõe e persiste preferências do usuário."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, QStandardPaths, QUrl, Signal, Slot

from scrcpy_ui.storage.settings_store import SettingsStore

_SCREENSHOT_DIR_KEY = "screenshot_dir"
_RECORDING_DIR_KEY = "recording_dir"
_STAY_AWAKE_KEY = "stay_awake"
_SHOW_TOUCHES_KEY = "show_touches"
_AUDIO_ENABLED_KEY = "audio_enabled"
_AUDIO_CODEC_KEY = "audio_codec"
_VIDEO_CODEC_KEY = "video_codec"
_MAX_SIZE_KEY = "max_size"
_VIDEO_BIT_RATE_KEY = "video_bit_rate"
_MAX_FPS_KEY = "max_fps"
_AUTO_CONNECT_SINGLE_DEVICE_KEY = "auto_connect_single_device"
_THEME_MODE_KEY = "theme_mode"
_INSPECTOR_OPEN_BY_DEFAULT_KEY = "inspector_open_by_default"

AUDIO_CODECS = ("opus", "aac", "flac", "raw")
VIDEO_CODECS = ("h264", "h265", "av1")
THEME_MODES = ("system", "light", "dark")


def _default_screenshot_dir() -> str:
    pictures = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
    return str(Path(pictures) / "scrcpy-ui")


def _default_recording_dir() -> str:
    movies = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MoviesLocation)
    return str(Path(movies) / "scrcpy-ui")


class SettingsViewModel(QObject):
    screenshotDirChanged = Signal(str)
    recordingDirChanged = Signal(str)
    stayAwakeChanged = Signal(bool)
    showTouchesChanged = Signal(bool)
    audioEnabledChanged = Signal(bool)
    audioCodecChanged = Signal(str)
    videoCodecChanged = Signal(str)
    maxSizeChanged = Signal(int)
    videoBitRateChanged = Signal(int)
    maxFpsChanged = Signal(int)
    autoConnectSingleDeviceChanged = Signal(bool)
    inspectorOpenByDefaultChanged = Signal(bool)
    themeModeChanged = Signal(str)

    def __init__(self, store: SettingsStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._screenshot_dir = self._store.get(_SCREENSHOT_DIR_KEY, _default_screenshot_dir())
        self._recording_dir = self._store.get(_RECORDING_DIR_KEY, _default_recording_dir())
        self._stay_awake = self._store.get(_STAY_AWAKE_KEY, "0") == "1"
        self._show_touches = self._store.get(_SHOW_TOUCHES_KEY, "0") == "1"
        self._audio_enabled = self._store.get(_AUDIO_ENABLED_KEY, "1") == "1"
        self._audio_codec = self._store.get(_AUDIO_CODEC_KEY, "opus")
        if self._audio_codec not in AUDIO_CODECS:
            self._audio_codec = "opus"
        self._video_codec = self._store.get(_VIDEO_CODEC_KEY, "h264")
        if self._video_codec not in VIDEO_CODECS:
            self._video_codec = "h264"
        self._max_size = int(self._store.get(_MAX_SIZE_KEY, "0"))
        self._video_bit_rate = int(self._store.get(_VIDEO_BIT_RATE_KEY, "8000000"))
        self._max_fps = int(self._store.get(_MAX_FPS_KEY, "0"))
        self._auto_connect_single_device = (
            # Padrão desligado: o usuário escolhe na grade qual device abrir
            self._store.get(_AUTO_CONNECT_SINGLE_DEVICE_KEY, "0") == "1"
        )
        self._inspector_open_by_default = (
            self._store.get(_INSPECTOR_OPEN_BY_DEFAULT_KEY, "1") == "1"  # padrão ligado
        )
        self._theme_mode = self._store.get(_THEME_MODE_KEY, "system")
        if self._theme_mode not in THEME_MODES:
            self._theme_mode = "system"

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

    @Property(str, notify=recordingDirChanged)
    def recordingDir(self) -> str:
        return self._recording_dir

    @Slot(QUrl)
    def setRecordingDir(self, folder_url: QUrl) -> None:
        path = folder_url.toLocalFile()
        if not path or path == self._recording_dir:
            return
        self._recording_dir = path
        self._store.set(_RECORDING_DIR_KEY, path)
        self.recordingDirChanged.emit(path)

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

    @Property(str, notify=videoCodecChanged)
    def videoCodec(self) -> str:
        return self._video_codec

    @videoCodec.setter
    def videoCodec(self, value: str) -> None:
        if value == self._video_codec or value not in VIDEO_CODECS:
            return
        self._video_codec = value
        self._store.set(_VIDEO_CODEC_KEY, value)
        self.videoCodecChanged.emit(value)

    @Property(int, notify=maxSizeChanged)
    def maxSize(self) -> int:
        return self._max_size

    @maxSize.setter
    def maxSize(self, value: int) -> None:
        if value == self._max_size:
            return
        self._max_size = value
        self._store.set(_MAX_SIZE_KEY, str(value))
        self.maxSizeChanged.emit(value)

    @Property(int, notify=videoBitRateChanged)
    def videoBitRate(self) -> int:
        return self._video_bit_rate

    @videoBitRate.setter
    def videoBitRate(self, value: int) -> None:
        if value == self._video_bit_rate:
            return
        self._video_bit_rate = value
        self._store.set(_VIDEO_BIT_RATE_KEY, str(value))
        self.videoBitRateChanged.emit(value)

    @Property(int, notify=maxFpsChanged)
    def maxFps(self) -> int:
        return self._max_fps

    @maxFps.setter
    def maxFps(self, value: int) -> None:
        if value == self._max_fps:
            return
        self._max_fps = value
        self._store.set(_MAX_FPS_KEY, str(value))
        self.maxFpsChanged.emit(value)

    @Property(bool, notify=autoConnectSingleDeviceChanged)
    def autoConnectSingleDevice(self) -> bool:
        return self._auto_connect_single_device

    @autoConnectSingleDevice.setter
    def autoConnectSingleDevice(self, value: bool) -> None:
        if value == self._auto_connect_single_device:
            return
        self._auto_connect_single_device = value
        self._store.set(_AUTO_CONNECT_SINGLE_DEVICE_KEY, "1" if value else "0")
        self.autoConnectSingleDeviceChanged.emit(value)

    # Abrir o espelhamento já com o painel da hierarquia da tela aberto
    @Property(bool, notify=inspectorOpenByDefaultChanged)
    def inspectorOpenByDefault(self) -> bool:
        return self._inspector_open_by_default

    @inspectorOpenByDefault.setter
    def inspectorOpenByDefault(self, value: bool) -> None:
        if value == self._inspector_open_by_default:
            return
        self._inspector_open_by_default = value
        self._store.set(_INSPECTOR_OPEN_BY_DEFAULT_KEY, "1" if value else "0")
        self.inspectorOpenByDefaultChanged.emit(value)

    @Property(str, notify=themeModeChanged)
    def themeMode(self) -> str:
        return self._theme_mode

    @themeMode.setter
    def themeMode(self, value: str) -> None:
        if value == self._theme_mode or value not in THEME_MODES:
            return
        self._theme_mode = value
        self._store.set(_THEME_MODE_KEY, value)
        self.themeModeChanged.emit(value)
