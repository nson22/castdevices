"""Grava a sessão (vídeo + áudio, se ativo) direto num container MKV, sem
re-decodificar/re-encodificar -- os mesmos pacotes já codificados que vão pra
tela/pro QAudioSink também são "remuxados" aqui.

MKV foi escolhido porque aceita H.264/H.265/AV1 e opus/aac/flac/PCM em
Annex-B/bitstream crus diretamente. MP4 exigiria converter o vídeo pra AVCC
(NALUs com length-prefix + extradata separado), o que não está implementado
nesta fase.
"""

from __future__ import annotations

import threading
from fractions import Fraction

import av

from scrcpy_ui.protocol.audio_stream import AudioPacket
from scrcpy_ui.protocol.constants import VIDEO_DECODER_NAMES
from scrcpy_ui.protocol.video_stream import VideoPacket

_AUDIO_MUX_CODECS = {
    "opus": "opus",
    "aac": "aac",
    "flac": "flac",
    "raw": "pcm_s16le",
}

# pts/dts do scrcpy vêm em microssegundos -- fixo, nunca ler de volta de
# stream.time_base: o muxer matroska reescreve o time_base do stream pra
# 1/1000 (granularidade nativa dele) assim que o primeiro pacote é escrito,
# e usar esse valor já coagido pros pacotes seguintes infla os timestamps em
# 1000x (foi exatamente a causa da tela preta ao dar play).
_PTS_TIME_BASE = Fraction(1, 1_000_000)


class SessionRecorder:
    def __init__(
        self,
        path: str,
        video_codec: str,
        width: int,
        height: int,
        audio_codec: str | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self._container = av.open(path, mode="w", format="matroska")

        decoder_name = VIDEO_DECODER_NAMES.get(video_codec, video_codec)
        self._video_stream = self._container.add_stream(decoder_name)
        self._video_stream.width = width
        self._video_stream.height = height
        self._video_started = False
        # O pts que vem do device é um timestamp bruto do clock de uptime do
        # aparelho (ex.: ~540000s = horas ligado), não relativo ao início da
        # gravação. Sem reajustar pra zero, o arquivo fica com start_time/
        # duration absurdos e a maioria dos players mostra tela preta porque
        # não acham nenhum frame em t=0. Por isso tudo é escrito relativo ao
        # pts do primeiro keyframe.
        self._pts_offset: int | None = None

        self._audio_codec = audio_codec
        self._audio_stream = None
        if audio_codec:
            self._audio_stream = self._container.add_stream(
                _AUDIO_MUX_CODECS[audio_codec], rate=48000
            )

    def write_video(self, packet: VideoPacket) -> None:
        if packet.is_config:
            return
        if not self._video_started:
            if not packet.is_key:
                return  # precisa comecar a gravação num keyframe
            self._video_started = True
            self._pts_offset = packet.pts
        with self._lock:
            self._mux(packet.data, packet.pts - self._pts_offset, self._video_stream, packet.is_key)

    def write_audio(self, packet: AudioPacket) -> None:
        if self._audio_stream is None:
            return
        if packet.is_config:
            if self._audio_codec == "aac":
                self._audio_stream.codec_context.extradata = packet.data
            return
        if self._pts_offset is None or packet.pts < self._pts_offset:
            return  # vídeo ainda não achou o primeiro keyframe -- descarta
        with self._lock:
            self._mux(packet.data, packet.pts - self._pts_offset, self._audio_stream, True)

    def _mux(self, data: bytes, pts: int, stream: av.stream.Stream, is_key: bool) -> None:
        av_packet = av.Packet(data)
        av_packet.pts = pts
        av_packet.dts = pts
        av_packet.time_base = _PTS_TIME_BASE
        av_packet.stream = stream
        if is_key:
            av_packet.is_keyframe = True
        self._container.mux(av_packet)

    def close(self) -> None:
        with self._lock:
            self._container.close()
