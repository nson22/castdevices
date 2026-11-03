"""Decodificação H.264 (Annex B) dos pacotes do scrcpy via PyAV."""

from __future__ import annotations

import av

from scrcpy_ui.protocol.video_stream import VideoPacket


class H264Decoder:
    def __init__(self) -> None:
        self._codec_ctx = av.CodecContext.create("h264", "r")

    def decode(self, packet: VideoPacket) -> list[av.VideoFrame]:
        av_packet = av.Packet(packet.data)
        return list(self._codec_ctx.decode(av_packet))
