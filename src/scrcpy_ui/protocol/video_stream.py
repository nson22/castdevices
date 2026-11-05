"""Leitura do framing de pacotes de vídeo do scrcpy (header de 12 bytes + payload).

Pacotes de config (SPS/PPS no H.264, VPS/SPS/PPS no H.265) precisam ser
mesclados com o próximo pacote de mídia antes de ir para o decoder -- enviá-los
sozinhos para o avcodec causa "Invalid data found when processing input"
(validado em scripts/spike_handshake.py + probing manual). Isso só vale pra
H.264/H.265; outros codecs (av1) não mesclam -- ver VIDEO_CODECS_WITH_CONFIG_MERGE.
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
    SESSION_PACKET_MSB,
    VIDEO_CODECS_WITH_CONFIG_MERGE,
)


@dataclass
class VideoPacket:
    is_key: bool
    is_config: bool
    pts: int
    data: bytes


@dataclass
class VideoSession:
    """Nova sessão de captura: o tamanho do vídeo mudou (ex.: device girou).
    O server reinicia o encoder e manda config + keyframe novos em seguida."""

    width: int
    height: int
    client_resized: bool


def iter_video_packets(
    video_sock: socket.socket, codec: str = "h264"
) -> Iterator[VideoPacket | VideoSession]:
    """Pacotes de mídia e, a cada mudança de tamanho, um VideoSession.

    Protocolo do scrcpy 4.0: o MSB do header distingue um *pacote de sessão*
    (só os 12 bytes do header, SEM payload: flags u32, largura u32, altura
    u32) de um *pacote de mídia* (pts/flags u64, tamanho u32, payload). Ler o
    de sessão como mídia consome bytes do frame seguinte e desalinha o stream
    inteiro (frame verde e vídeo travado depois de girar a tela).
    """
    merge_config = codec in VIDEO_CODECS_WITH_CONFIG_MERGE
    pending_config = b""
    while True:
        header = recv_exact(video_sock, PACKET_HEADER_SIZE)
        if header[0] & SESSION_PACKET_MSB:
            flags, width, height = struct.unpack(">III", header)
            pending_config = b""  # config da sessão anterior não vale mais
            yield VideoSession(width=width, height=height, client_resized=bool(flags & 1))
            continue

        pts_flags, length = struct.unpack(">QI", header)
        is_config = bool(pts_flags & PACKET_FLAG_CONFIG)
        is_key = bool(pts_flags & PACKET_FLAG_KEY_FRAME)
        pts = pts_flags & PACKET_PTS_MASK
        payload = recv_exact(video_sock, length)

        if is_config and merge_config:
            pending_config += payload
            continue

        if pending_config:
            payload = pending_config + payload
            pending_config = b""

        yield VideoPacket(is_key=is_key, is_config=is_config, pts=pts, data=payload)
