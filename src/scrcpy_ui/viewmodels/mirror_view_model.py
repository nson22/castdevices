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

import av
from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtMultimedia import QVideoFrame, QVideoSink

from scrcpy_ui.adb import client
from scrcpy_ui.audio.decoder import AudioDecoder
from scrcpy_ui.audio.player import AudioPlayer
from scrcpy_ui.input.keyboard_mapper import qt_key_to_android_keycode
from scrcpy_ui.input.mouse_mapper import MouseMapper
from scrcpy_ui.protocol.audio_stream import iter_audio_packets
from scrcpy_ui.protocol.connection import ScrcpyConnection
from scrcpy_ui.protocol.constants import (
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
from scrcpy_ui.video.change_detector import ScreenChangeDetector
from scrcpy_ui.video.decoder import VideoDecoder
from scrcpy_ui.video.frame_bridge import av_frame_to_qvideoframe
from scrcpy_ui.video.recorder import SessionRecorder
from scrcpy_ui.viewmodels.settings_view_model import SettingsViewModel


class MirrorViewModel(QObject):
    connected = Signal(str, int, int)
    disconnected = Signal()
    errorOccurred = Signal(str)
    frameReady = Signal(QVideoFrame)
    # Conteúdo da tela mudou de fato (frames repetidos com a tela parada não contam)
    screenContentChanged = Signal()
    screenshotSaved = Signal(str)
    clipboardReceived = Signal(str)
    screenPowerChanged = Signal(bool)
    audioDataReady = Signal(bytes)
    recordingChanged = Signal(bool)
    recordingSaved = Signal(str)
    connectionChanged = Signal()

    def __init__(self, settings_view_model: SettingsViewModel, parent=None):
        super().__init__(parent)
        self._settings = settings_view_model
        self._connection: ScrcpyConnection | None = None
        self._control_sender: ControlSender | None = None
        self._mouse_mapper: MouseMapper | None = None
        self._video_sink: QVideoSink | None = None
        self._sink_token = 0
        self._worker: threading.Thread | None = None
        self._audio_thread: threading.Thread | None = None
        self._last_frame: QVideoFrame | None = None
        self._screen_on = True
        self._audio_player = AudioPlayer(self)
        self._audio_active = False
        self._session_video_codec: str | None = None
        self._session_width = 0
        self._session_height = 0
        self._recorder: SessionRecorder | None = None
        self._recording_path: Path | None = None

        self.frameReady.connect(self._on_frame_ready)
        self.clipboardReceived.connect(self._on_clipboard_received)
        self.audioDataReady.connect(self._audio_player.write)
        self.connected.connect(self._on_connected)
        self.disconnected.connect(self._on_disconnected)

    @Slot(QVideoSink)
    def attachVideoSink(self, sink: QVideoSink) -> None:
        self._video_sink = sink
        self._sink_token += 1
        token = self._sink_token
        # O sink morre junto com o VideoOutput (tela saiu da pilha, ou engine
        # recriada no hot reload). Só esquece se ainda for o atual: no reload a
        # tela nova já registrou o dela antes de a antiga ser destruída.
        sink.destroyed.connect(lambda *_: self._forget_video_sink(token))
        # O scrcpy só manda frame quando a tela do device muda: sem isso, uma
        # tela recriada fica preta até algo mexer no device.
        if self._last_frame is not None:
            sink.setVideoFrame(self._last_frame)

    def _forget_video_sink(self, token: int) -> None:
        if token == self._sink_token:
            self._video_sink = None

    @Property(bool, notify=connectionChanged)
    def isConnected(self) -> bool:
        return self._connection is not None

    @Property(str, notify=connectionChanged)
    def deviceSerial(self) -> str:
        return self._connection.device.serial if self._connection is not None else ""

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

    def shutdown(self) -> None:
        """App fechando: finaliza a gravação (senão o .mkv fica sem o trailer
        e corrompido) e encerra a sessão esperando as threads de leitura
        terminarem enquanto os objetos Qt ainda existem -- sem isso elas
        emitem sinais num objeto já destruído durante o encerramento."""
        self._stop_recording_internal()
        self.disconnectDevice()
        for thread in (self._worker, self._audio_thread):
            if thread is not None:
                thread.join(timeout=2)

    def _run(self, serial: str) -> None:
        audio_enabled = self._settings.audioEnabled
        audio_codec = self._settings.audioCodec
        video_codec = self._settings.videoCodec
        connection = ScrcpyConnection(client.get_device(serial))
        try:
            info = connection.open(
                stay_awake=self._settings.stayAwake,
                show_touches=self._settings.showTouches,
                audio=audio_enabled,
                audio_codec=audio_codec,
                video_codec=video_codec,
                max_size=self._settings.maxSize,
                video_bit_rate=self._settings.videoBitRate,
                max_fps=self._settings.maxFps,
            )
        except Exception as exc:
            self.errorOccurred.emit(str(exc))
            return

        self._connection = connection
        self._control_sender = ControlSender(connection.control_sock)
        self._mouse_mapper = MouseMapper(info.width, info.height)
        self._audio_active = audio_enabled and connection.audio_sock is not None
        self._session_video_codec = video_codec
        self._session_width = info.width
        self._session_height = info.height
        self.connected.emit(info.name, info.width, info.height)

        device_msg_thread = threading.Thread(
            target=self._drain_device_messages, daemon=True
        )
        device_msg_thread.start()

        if self._audio_active:
            self._audio_thread = threading.Thread(
                target=self._read_audio, args=(connection, audio_codec), daemon=True
            )
            self._audio_thread.start()

        decoder = VideoDecoder(video_codec)
        change_detector = ScreenChangeDetector()
        try:
            for packet in iter_video_packets(connection.video_sock, video_codec):
                if self._recorder is not None:
                    self._recorder.write_video(packet)
                for frame in decoder.decode(packet):
                    self.frameReady.emit(av_frame_to_qvideoframe(frame))
                    if change_detector.changed(frame):
                        self.screenContentChanged.emit()
        except (ConnectionError, OSError):
            pass
        except av.error.FFmpegError as exc:
            self.errorOccurred.emit(
                f"Erro decodificando vídeo ({video_codec}): {exc}. "
                "O device pode suportar esse codec via hardware, mas o decoder "
                "pode não estar disponível nesta instalação."
            )
        finally:
            self._stop_recording_internal()
            connection.close()
            self._connection = None
            self._control_sender = None
            self.disconnected.emit()

    def _read_audio(self, connection: ScrcpyConnection, codec: str) -> None:
        if connection.audio_sock is None:
            return
        decoder = None if codec == "raw" else AudioDecoder(codec)
        try:
            for packet in iter_audio_packets(connection.audio_sock):
                if self._recorder is not None:
                    self._recorder.write_audio(packet)
                pcm = packet.data if decoder is None else decoder.decode(packet)
                if pcm:
                    self.audioDataReady.emit(pcm)
        except (ConnectionError, OSError):
            pass
        except av.error.FFmpegError as exc:
            self.errorOccurred.emit(f"Erro decodificando áudio ({codec}): {exc}")

    @Slot(str, int, int)
    def _on_connected(self, name: str, width: int, height: int) -> None:
        if self._audio_active:
            self._audio_player.start()
        self.connectionChanged.emit()

    @Slot()
    def _on_disconnected(self) -> None:
        self._audio_player.stop()
        self._audio_active = False
        self._last_frame = None
        self.connectionChanged.emit()

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

    @Property(bool, notify=recordingChanged)
    def isRecording(self) -> bool:
        return self._recorder is not None

    @Slot()
    def toggleRecording(self) -> None:
        if self._recorder is not None:
            self._stop_recording_internal()
            return
        if self._connection is None or self._session_video_codec is None:
            self.errorOccurred.emit("Conecte num device antes de gravar")
            return
        recording_dir = Path(self._settings.recordingDir)
        recording_dir.mkdir(parents=True, exist_ok=True)
        path = recording_dir / f"scrcpy-ui_{datetime.now():%Y%m%d_%H%M%S}.mkv"
        try:
            self._recorder = SessionRecorder(
                str(path),
                self._session_video_codec,
                self._session_width,
                self._session_height,
                audio_codec=self._settings.audioCodec if self._audio_active else None,
            )
        except Exception as exc:
            self.errorOccurred.emit(f"Falha ao iniciar gravação: {exc}")
            return
        self._recording_path = path
        self.recordingChanged.emit(True)

    def _stop_recording_internal(self) -> None:
        recorder = self._recorder
        if recorder is None:
            return
        # Zera a referência ANTES de fechar: assim as threads de vídeo/áudio
        # (que checam "self._recorder is not None" antes de cada escrita) já
        # param de tentar escrever antes do close(); o lock interno do
        # SessionRecorder cobre qualquer escrita que já estava em andamento.
        self._recorder = None
        recorder.close()
        if self._recording_path is not None:
            self.recordingSaved.emit(str(self._recording_path))
        self._recording_path = None
        self.recordingChanged.emit(False)

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
