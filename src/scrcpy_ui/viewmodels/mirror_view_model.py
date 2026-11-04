"""ViewModel da tela de espelhamento: orquestra conexão, decode e input para
um device (camada de Model/serviços em adb/, protocol/ e video/).

A leitura do socket de vídeo + decode roda numa worker thread; o envio de
controle (touch/tecla) acontece direto na thread principal (chamado pelos
slots do QML) já que é um socket TCP local (loopback via adb reverse), então
o custo do `sendall` bloqueante é desprezível.
"""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtMultimedia import QVideoFrame, QVideoSink

from scrcpy_ui.adb import client
from scrcpy_ui.input.keyboard_mapper import qt_key_to_android_keycode
from scrcpy_ui.input.mouse_mapper import MouseMapper
from scrcpy_ui.protocol.connection import ScrcpyConnection
from scrcpy_ui.protocol.constants import (
    ANDROID_KEYCODE_APP_SWITCH,
    ANDROID_KEYCODE_HOME,
    ControlMsgType,
    CopyKey,
    DeviceMsgType,
    KeyEventAction,
    MotionEventAction,
)
from scrcpy_ui.protocol.control_stream import (
    ControlSender,
    iter_device_messages,
    serialize_back_or_screen_on,
    serialize_get_clipboard,
    serialize_key_event,
    serialize_scroll_event,
    serialize_set_clipboard,
    serialize_set_display_power,
    serialize_simple,
    serialize_touch_event,
)
from scrcpy_ui.protocol.video_stream import iter_video_packets
from scrcpy_ui.video.decoder import H264Decoder
from scrcpy_ui.video.frame_bridge import av_frame_to_qvideoframe
from scrcpy_ui.viewmodels.settings_view_model import SettingsViewModel


class MirrorViewModel(QObject):
    connected = Signal(str, int, int)
    disconnected = Signal()
    errorOccurred = Signal(str)
    frameReady = Signal(QVideoFrame)
    screenshotSaved = Signal(str)
    clipboardReceived = Signal(str)
    screenPowerChanged = Signal(bool)

    def __init__(self, settings_view_model: SettingsViewModel, parent=None):
        super().__init__(parent)
        self._settings = settings_view_model
        self._connection: ScrcpyConnection | None = None
        self._control_sender: ControlSender | None = None
        self._mouse_mapper: MouseMapper | None = None
        self._video_sink: QVideoSink | None = None
        self._worker: threading.Thread | None = None
        self._last_frame: QVideoFrame | None = None
        self._screen_on = True

        self.frameReady.connect(self._on_frame_ready)
        self.clipboardReceived.connect(self._on_clipboard_received)

    @Slot(QVideoSink)
    def attachVideoSink(self, sink: QVideoSink) -> None:
        self._video_sink = sink

    @Slot(str)
    def connectToDevice(self, serial: str) -> None:
        if self._worker is not None and self._worker.is_alive():
            return
        self._worker = threading.Thread(target=self._run, args=(serial,), daemon=True)
        self._worker.start()

    @Slot()
    def disconnectDevice(self) -> None:
        if self._connection is not None:
            self._connection.close()

    def _run(self, serial: str) -> None:
        connection = ScrcpyConnection(client.get_device(serial))
        try:
            info = connection.open(
                stay_awake=self._settings.stayAwake,
                show_touches=self._settings.showTouches,
            )
        except Exception as exc:
            self.errorOccurred.emit(str(exc))
            return

        self._connection = connection
        self._control_sender = ControlSender(connection.control_sock)
        self._mouse_mapper = MouseMapper(info.width, info.height)
        self.connected.emit(info.name, info.width, info.height)

        device_msg_thread = threading.Thread(
            target=self._drain_device_messages, daemon=True
        )
        device_msg_thread.start()

        decoder = H264Decoder()
        try:
            for packet in iter_video_packets(connection.video_sock):
                for frame in decoder.decode(packet):
                    self.frameReady.emit(av_frame_to_qvideoframe(frame))
        except (ConnectionError, OSError):
            pass
        finally:
            connection.close()
            self._connection = None
            self._control_sender = None
            self.disconnected.emit()

    def _drain_device_messages(self) -> None:
        connection = self._connection
        if connection is None or connection.control_sock is None:
            return
        try:
            for msg_type, payload in iter_device_messages(connection.control_sock):
                if msg_type == DeviceMsgType.CLIPBOARD:
                    self.clipboardReceived.emit(payload.decode("utf-8", errors="replace"))
        except (ConnectionError, OSError):
            pass

    @Slot(str)
    def _on_clipboard_received(self, text: str) -> None:
        QGuiApplication.clipboard().setText(text)

    @Slot(QVideoFrame)
    def _on_frame_ready(self, frame: QVideoFrame) -> None:
        self._last_frame = frame
        if self._video_sink is not None:
            self._video_sink.setVideoFrame(frame)

    @Slot()
    def takeScreenshot(self) -> None:
        if self._last_frame is None:
            self.errorOccurred.emit("Nenhum frame disponível para screenshot ainda")
            return
        image = self._last_frame.toImage()
        screenshot_dir = Path(self._settings.screenshotDir)
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        path = screenshot_dir / f"scrcpy-ui_{datetime.now():%Y%m%d_%H%M%S}.png"
        if image.save(str(path)):
            self.screenshotSaved.emit(str(path))
        else:
            self.errorOccurred.emit(f"Falha ao salvar screenshot em {path}")

    @Slot(float, float, float, float)
    def setContentRect(self, x: float, y: float, width: float, height: float) -> None:
        if self._mouse_mapper is not None:
            self._mouse_mapper.set_content_rect(x, y, width, height)

    def _send_touch(self, action: int, item_x: float, item_y: float, qt_buttons: int) -> None:
        if self._mouse_mapper is None or self._control_sender is None:
            return
        point = self._mouse_mapper.map_point(item_x, item_y)
        if point is None:
            return
        dev_x, dev_y = point
        buttons = MouseMapper.qt_buttons_to_android(qt_buttons)
        data = serialize_touch_event(
            action,
            dev_x,
            dev_y,
            self._mouse_mapper.device_width,
            self._mouse_mapper.device_height,
            action_button=buttons,
            buttons=buttons,
            pressure=1.0 if action != MotionEventAction.UP else 0.0,
        )
        try:
            self._control_sender.send(data)
        except OSError:
            pass

    @Slot(float, float, int)
    def sendMousePress(self, item_x: float, item_y: float, qt_buttons: int) -> None:
        self._send_touch(MotionEventAction.DOWN, item_x, item_y, qt_buttons)

    @Slot(float, float, int)
    def sendMouseMove(self, item_x: float, item_y: float, qt_buttons: int) -> None:
        self._send_touch(MotionEventAction.MOVE, item_x, item_y, qt_buttons)

    @Slot(float, float, int)
    def sendMouseRelease(self, item_x: float, item_y: float, qt_buttons: int) -> None:
        self._send_touch(MotionEventAction.UP, item_x, item_y, qt_buttons)

    @Slot(float, float, float, float)
    def sendWheel(self, item_x: float, item_y: float, delta_x: float, delta_y: float) -> None:
        if self._mouse_mapper is None or self._control_sender is None:
            return
        point = self._mouse_mapper.map_point(item_x, item_y)
        if point is None:
            return
        dev_x, dev_y = point
        data = serialize_scroll_event(
            dev_x,
            dev_y,
            self._mouse_mapper.device_width,
            self._mouse_mapper.device_height,
            delta_x,
            delta_y,
        )
        try:
            self._control_sender.send(data)
        except OSError:
            pass

    @Slot(int, bool)
    def sendKey(self, qt_key: int, pressed: bool) -> None:
        if self._control_sender is None:
            return
        keycode = qt_key_to_android_keycode(qt_key)
        if keycode is None:
            return
        action = KeyEventAction.DOWN if pressed else KeyEventAction.UP
        data = serialize_key_event(action, keycode)
        try:
            self._control_sender.send(data)
        except OSError:
            pass

    @Slot()
    def sendBack(self) -> None:
        """Botão direito do mouse: Android não tem um gesto de "clique direito"
        nativo pra toque, então -- igual ao scrcpy original -- isso simula a
        tecla Voltar em vez de injetar um toque com o botão secundário."""
        if self._control_sender is None:
            return
        try:
            self._control_sender.send(serialize_back_or_screen_on(KeyEventAction.DOWN))
            self._control_sender.send(serialize_back_or_screen_on(KeyEventAction.UP))
        except OSError:
            pass

    @Slot()
    def sendHome(self) -> None:
        """Clique do botão do meio (wheel): simula a tecla Home, mesmo
        binding padrão do scrcpy original para esse botão."""
        if self._control_sender is None:
            return
        try:
            self._control_sender.send(serialize_key_event(KeyEventAction.DOWN, ANDROID_KEYCODE_HOME))
            self._control_sender.send(serialize_key_event(KeyEventAction.UP, ANDROID_KEYCODE_HOME))
        except OSError:
            pass

    @Slot()
    def sendRecents(self) -> None:
        if self._control_sender is None:
            return
        try:
            self._control_sender.send(
                serialize_key_event(KeyEventAction.DOWN, ANDROID_KEYCODE_APP_SWITCH)
            )
            self._control_sender.send(
                serialize_key_event(KeyEventAction.UP, ANDROID_KEYCODE_APP_SWITCH)
            )
        except OSError:
            pass

    @Slot()
    def rotateDevice(self) -> None:
        if self._control_sender is None:
            return
        try:
            self._control_sender.send(serialize_simple(ControlMsgType.ROTATE_DEVICE))
        except OSError:
            pass

    @Slot()
    def expandNotifications(self) -> None:
        if self._control_sender is None:
            return
        try:
            self._control_sender.send(serialize_simple(ControlMsgType.EXPAND_NOTIFICATION_PANEL))
        except OSError:
            pass

    @Property(bool, notify=screenPowerChanged)
    def screenOn(self) -> bool:
        return self._screen_on

    @Slot()
    def toggleScreenPower(self) -> None:
        if self._control_sender is None:
            return
        self._screen_on = not self._screen_on
        try:
            self._control_sender.send(serialize_set_display_power(self._screen_on))
        except OSError:
            pass
        self.screenPowerChanged.emit(self._screen_on)

    @Slot()
    def copyClipboardFromDevice(self) -> None:
        if self._control_sender is None:
            return
        try:
            self._control_sender.send(serialize_get_clipboard(CopyKey.COPY))
        except OSError:
            pass

    @Slot()
    def pasteClipboardToDevice(self) -> None:
        if self._control_sender is None:
            return
        text = QGuiApplication.clipboard().text()
        if not text:
            return
        try:
            self._control_sender.send(serialize_set_clipboard(0, text, paste=True))
        except OSError:
            pass
