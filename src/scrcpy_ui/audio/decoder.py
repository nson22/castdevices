"""Decodificação de áudio (opus/aac/flac) + resample pra PCM s16 stereo 48kHz
(formato que o AudioPlayer / QAudioSink espera). "raw" não precisa de decoder
nenhum -- o payload já é PCM S16LE stereo 48kHz direto do device.
"""

from __future__ import annotations

import av

from scrcpy_ui.protocol.audio_stream import AudioPacket
from scrcpy_ui.protocol.constants import AUDIO_CHANNELS, AUDIO_SAMPLE_RATE


class AudioDecoder:
    def __init__(self, codec_name: str) -> None:
        self._codec_name = codec_name
        self._codec_ctx = av.CodecContext.create(codec_name, "r")
        self._resampler = av.AudioResampler(
            format="s16", layout="stereo", rate=AUDIO_SAMPLE_RATE
        )

    def decode(self, packet: AudioPacket) -> bytes:
        """Retorna PCM s16 interleaved pronto pra tocar (pode ser vazio)."""
        if packet.is_config:
            # AAC manda o AudioSpecificConfig como pacote de config -- o
            # decoder precisa dele como extradata antes do primeiro decode()
            # (opus e flac decodificam sem precisar disso).
            if self._codec_name == "aac":
                self._codec_ctx.extradata = packet.data
            return b""
        av_packet = av.Packet(packet.data)
        pcm = bytearray()
        for frame in self._codec_ctx.decode(av_packet):
            for resampled in self._resampler.resample(frame):
                pcm += resampled.to_ndarray().tobytes()
        return bytes(pcm)


assert AUDIO_CHANNELS == 2  # resampler acima está fixo em "stereo"
