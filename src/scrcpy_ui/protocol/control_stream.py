"""Serialização das mensagens de controle (touch/tecla/scroll) e leitura das
mensagens que o device manda de volta (clipboard), conforme control_msg.c /
device_msg.c do scrcpy (tag v4.0).
"""

from __future__ import annotations

import socket
import struct
import threading
from typing import Iterator

from scrcpy_ui.protocol.connection import recv_exact
from scrcpy_ui.protocol.constants import ControlMsgType, DeviceMsgType, POINTER_ID_MOUSE


def _float_to_u16fp(f: float) -> int:
    u = int(f * 0x1_0000)
    return min(u, 0xFFFF)


def _float_to_i16fp(f: float) -> int:
    i = int(f * 0x8000)
    return max(-0x8000, min(i, 0x7FFF))


def _write_position(x: int, y: int, screen_w: int, screen_h: int) -> bytes:
    return struct.pack(">iiHH", x, y, screen_w, screen_h)


def serialize_touch_event(
    action: int,
    x: int,
    y: int,
    screen_w: int,
    screen_h: int,
    *,
    pointer_id: int = POINTER_ID_MOUSE,
    pressure: float = 1.0,
    action_button: int = 0,
    buttons: int = 0,
) -> bytes:
    return (
        struct.pack(">BBQ", ControlMsgType.INJECT_TOUCH_EVENT, action, pointer_id)
        + _write_position(x, y, screen_w, screen_h)
        + struct.pack(">HII", _float_to_u16fp(pressure), action_button, buttons)
    )


def serialize_scroll_event(
    x: int,
    y: int,
    screen_w: int,
    screen_h: int,
    hscroll: float,
    vscroll: float,
    *,
    buttons: int = 0,
) -> bytes:
    hscroll_norm = max(-1.0, min(hscroll / 16, 1.0))
    vscroll_norm = max(-1.0, min(vscroll / 16, 1.0))
    return (
        struct.pack(">B", ControlMsgType.INJECT_SCROLL_EVENT)
        + _write_position(x, y, screen_w, screen_h)
        + struct.pack(
            ">hhI",
            _float_to_i16fp(hscroll_norm),
            _float_to_i16fp(vscroll_norm),
            buttons,
        )
    )


def serialize_key_event(action: int, keycode: int, *, repeat: int = 0, metastate: int = 0) -> bytes:
    return struct.pack(">BBIII", ControlMsgType.INJECT_KEYCODE, action, keycode, repeat, metastate)


class ControlSender:
    """Envio thread-safe de mensagens de controle pelo socket de controle."""

    def __init__(self, control_sock: socket.socket):
        self._sock = control_sock
        self._lock = threading.Lock()

    def send(self, data: bytes) -> None:
        with self._lock:
            self._sock.sendall(data)


def iter_device_messages(control_sock: socket.socket) -> Iterator[tuple[DeviceMsgType, bytes]]:
    """Gera (tipo, payload) para cada mensagem recebida do device (ex.: clipboard)."""
    while True:
        msg_type = DeviceMsgType(recv_exact(control_sock, 1)[0])
        if msg_type == DeviceMsgType.CLIPBOARD:
            length = struct.unpack(">I", recv_exact(control_sock, 4))[0]
            payload = recv_exact(control_sock, length)
        elif msg_type == DeviceMsgType.ACK_CLIPBOARD:
            payload = recv_exact(control_sock, 8)
        elif msg_type == DeviceMsgType.UHID_OUTPUT:
            header = recv_exact(control_sock, 4)
            size = struct.unpack(">H", header[2:4])[0]
            payload = header + recv_exact(control_sock, size)
        else:  # pragma: no cover - protocolo não deve mandar tipos desconhecidos
            raise ValueError(f"Tipo de device message desconhecido: {msg_type}")
        yield msg_type, payload
