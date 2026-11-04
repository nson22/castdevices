"""Decodificação de vídeo (h264/h265/av1) via PyAV."""

from __future__ import annotations

import av

from scrcpy_ui.protocol.constants import VIDEO_DECODER_NAMES
from scrcpy_ui.protocol.video_stream import VideoPacket


class VideoDecoder:
    def __init__(self, codec: str = "h264") -> None:
        self._codec = codec
        decoder_name = VIDEO_DECODER_NAMES.get(codec, codec)
        self._codec_ctx = av.CodecContext.create(decoder_name, "r")

    def decode(self, packet: VideoPacket) -> list[av.VideoFrame]:
        if packet.is_config:
            # Só chega aqui pra codecs sem merge de config (ver video_stream.py);
            # h264/h265 já vêm mesclados com o próximo pacote de mídia.
            self._codec_ctx.extradata = packet.data
            return []
        av_packet = av.Packet(packet.data)
        return list(self._codec_ctx.decode(av_packet))
