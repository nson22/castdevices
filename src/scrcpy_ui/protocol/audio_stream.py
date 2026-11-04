"""Framing dos pacotes de áudio do scrcpy.

Mesmo header de 12 bytes (PTS+flags de 8 bytes BE + tamanho de 4 bytes BE) do
vídeo, mas SEM session header antes do primeiro pacote, e SEM merge de
pacotes de config com o próximo pacote de mídia (isso só existe para H.264/
H.265 -- ver video_stream.py).
"""

from __future__ import annotations

import socket
import struct
from dataclasses import dataclass
from typing import Iterator

from scrcpy_ui.protocol.connection import recv_exact
from scrcpy_ui.protocol.constants import (
    PACKET_FLAG_CONFIG,
    PACKET_HEADER_SIZE,
    PACKET_PTS_MASK,
)


@dataclass
class AudioPacket:
    is_config: bool
    pts: int
    data: bytes


def iter_audio_packets(audio_sock: socket.socket) -> Iterator[AudioPacket]:
    while True:
        header = recv_exact(audio_sock, PACKET_HEADER_SIZE)
        pts_flags, length = struct.unpack(">QI", header)
        is_config = bool(pts_flags & PACKET_FLAG_CONFIG)
        pts = pts_flags & PACKET_PTS_MASK
        payload = recv_exact(audio_sock, length)
        yield AudioPacket(is_config=is_config, pts=pts, data=payload)
