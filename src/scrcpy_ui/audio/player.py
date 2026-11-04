"""Playback do áudio decodificado, via QAudioSink.

Precisa viver na thread principal (Qt Multimedia não é thread-safe pra isso);
o PCM chega via sinal Qt a partir da worker thread que decodifica.
"""

from __future__ import annotations

from PySide6.QtCore import QIODevice, QObject, Slot
from PySide6.QtMultimedia import QAudioFormat, QAudioSink

from scrcpy_ui.protocol.constants import AUDIO_CHANNELS, AUDIO_SAMPLE_RATE


class AudioPlayer(QObject):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        fmt = QAudioFormat()
        fmt.setSampleRate(AUDIO_SAMPLE_RATE)
        fmt.setChannelCount(AUDIO_CHANNELS)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        self._sink = QAudioSink(fmt, self)
        self._io_device: QIODevice | None = None

    def start(self) -> None:
        self._io_device = self._sink.start()

    @Slot(bytes)
    def write(self, pcm: bytes) -> None:
        if self._io_device is not None and pcm:
            self._io_device.write(pcm)

    def stop(self) -> None:
        self._sink.stop()
        self._io_device = None
