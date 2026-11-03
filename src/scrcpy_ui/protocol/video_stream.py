"""Leitura do framing de pacotes de vídeo do scrcpy (header de 12 bytes + payload).

Pacotes de config (SPS/PPS, sem slice de imagem) precisam ser mesclados com o
próximo pacote de mídia antes de ir para o decoder H.264 -- enviá-los sozinhos
para o avcodec causa "Invalid data found when processing input" (validado em
scripts/spike_handshake.py + probing manual). Essa mesclagem é feita aqui.
"""

from __future__ import annotations

import socket
import struct
from dataclasses import dataclass
from typing import Iterator

from scrcpy_ui.protocol.connection import recv_exact
from scrcpy_ui.protocol.constants import (
    PACKET_FLAG_CONFIG,
    PACKET_FLAG_KEY_FRAME,
    PACKET_HEADER_SIZE,
    PACKET_PTS_MASK,
)


@dataclass
class VideoPacket:
    is_key: bool
    pts: int
    data: bytes


def iter_video_packets(video_sock: socket.socket) -> Iterator[VideoPacket]:
    pending_config = b""
    while True:
        header = recv_exact(video_sock, PACKET_HEADER_SIZE)
        pts_flags, length = struct.unpack(">QI", header)
        is_config = bool(pts_flags & PACKET_FLAG_CONFIG)
        is_key = bool(pts_flags & PACKET_FLAG_KEY_FRAME)
        pts = pts_flags & PACKET_PTS_MASK
        payload = recv_exact(video_sock, length)

        if is_config:
            pending_config += payload
            continue

        if pending_config:
            payload = pending_config + payload
            pending_config = b""

        yield VideoPacket(is_key=is_key, pts=pts, data=payload)
