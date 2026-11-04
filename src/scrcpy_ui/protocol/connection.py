"""Abre o túnel adb + sockets de vídeo/áudio/controle para um device e faz o
handshake inicial.

Fluxo (modo "adb reverse", validado empiricamente em scripts/spike_handshake.py):
1. Garante o scrcpy-server.jar no device.
2. Bind num socket TCP local (porta efêmera) e `adb reverse` apontando pra ele.
3. Inicia o processo do server via `adb shell` (stream=True, mantido aberto pela sessão).
4. Aceita, NESSA ORDEM: video socket, áudio socket (se habilitado), control socket.
5. Remove o `adb reverse` (não é mais necessário, as conexões já existem).
6. Lê os 64 bytes do nome do device e o cabeçalho de sessão de vídeo (codec + w/h)
   do video socket, e (se habilitado) o codec id do áudio -- sem session header,
   só o vídeo tem um.
"""

from __future__ import annotations

import random
import socket
import struct
import threading
from dataclasses import dataclass

import adbutils

from scrcpy_ui.adb import server_deploy
from scrcpy_ui.protocol.constants import (
    AUDIO_CODEC_IDS,
    DEVICE_NAME_FIELD_LENGTH,
    VIDEO_CODEC_IDS,
)


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Conexão fechada pelo device")
        buf += chunk
    return bytes(buf)


@dataclass
class DeviceInfo:
    name: str
    width: int
    height: int


class ScrcpyConnection:
    def __init__(self, device: adbutils.AdbDevice):
        self.device = device
        self.video_sock: socket.socket | None = None
        self.audio_sock: socket.socket | None = None
        self.control_sock: socket.socket | None = None
        self.device_info: DeviceInfo | None = None
        self.audio_codec: str | None = None
        self.video_codec: str | None = None
        self._shell_conn: adbutils.AdbConnection | None = None
        self._drain_thread: threading.Thread | None = None

    def open(
        self,
        *,
        accept_timeout: float = 10.0,
        stay_awake: bool = False,
        show_touches: bool = False,
        audio: bool = False,
        audio_codec: str = "opus",
        video_codec: str = "h264",
        max_size: int = 0,
        video_bit_rate: int = 0,
        max_fps: int = 0,
    ) -> DeviceInfo:
        server_deploy.ensure_server_pushed(self.device)

        scid = random.getrandbits(31)
        socket_name = server_deploy.socket_name_for(scid)

        local_srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        local_srv.bind(("127.0.0.1", 0))
        local_srv.listen(3)
        local_port = local_srv.getsockname()[1]

        self.device.reverse(f"localabstract:{socket_name}", f"tcp:{local_port}")
        try:
            self._shell_conn = server_deploy.start_server(
                self.device,
                scid,
                stay_awake=stay_awake,
                show_touches=show_touches,
                audio=audio,
                audio_codec=audio_codec,
                video_codec=video_codec,
                max_size=max_size,
                video_bit_rate=video_bit_rate,
                max_fps=max_fps,
            )
            self._drain_thread = threading.Thread(
                target=self._drain_server_output, daemon=True
            )
            self._drain_thread.start()

            local_srv.settimeout(accept_timeout)
            try:
                # Ordem fixa do server: video, depois áudio (se habilitado), depois controle.
                self.video_sock, _ = local_srv.accept()
                if audio:
                    self.audio_sock, _ = local_srv.accept()
                self.control_sock, _ = local_srv.accept()
            except TimeoutError as exc:
                raise ConnectionError(
                    "Timeout esperando o scrcpy-server conectar (ver logs do server)"
                ) from exc
        finally:
            self.device.reverse_remove(f"localabstract:{socket_name}")
            local_srv.close()

        self.device_info = self._read_device_info(video_codec)
        self.video_codec = video_codec
        if audio:
            self.audio_codec = self._read_audio_codec(audio_codec)
        return self.device_info

    def _drain_server_output(self) -> None:
        assert self._shell_conn is not None
        try:
            while self._shell_conn.conn.recv(4096):
                pass
        except OSError:
            pass

    def _read_device_info(self, expected_video_codec: str) -> DeviceInfo:
        assert self.video_sock is not None
        name_buf = recv_exact(self.video_sock, DEVICE_NAME_FIELD_LENGTH)
        name = name_buf.split(b"\0", 1)[0].decode("utf-8", errors="replace")

        codec_id = struct.unpack(">I", recv_exact(self.video_sock, 4))[0]
        if codec_id != VIDEO_CODEC_IDS.get(expected_video_codec):
            raise RuntimeError(
                f"Codec de vídeo inesperado: 0x{codec_id:08x} "
                f"(esperava {expected_video_codec!r} -- device/encoder pode não suportar)"
            )

        header = recv_exact(self.video_sock, 12)
        width, height = struct.unpack(">II", header[4:12])
        return DeviceInfo(name=name, width=width, height=height)

    def _read_audio_codec(self, expected_codec: str) -> str:
        assert self.audio_sock is not None
        codec_id = struct.unpack(">I", recv_exact(self.audio_sock, 4))[0]
        if codec_id != AUDIO_CODEC_IDS.get(expected_codec):
            raise RuntimeError(
                f"Codec de áudio inesperado: 0x{codec_id:08x} (esperava {expected_codec!r})"
            )
        return expected_codec

    def close(self) -> None:
        """Idempotente -- tanto a worker thread (no finally, quando o socket
        cai) quanto disconnectDevice() (chamado da UI) podem chamar close()
        para a mesma conexão; adbutils.AdbConnection.close() não é seguro pra
        chamar duas vezes (dá AttributeError na segunda), daí zerar as
        referências depois de fechar."""
        for attr in ("video_sock", "audio_sock", "control_sock"):
            sock = getattr(self, attr)
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
                setattr(self, attr, None)
        if self._shell_conn is not None:
            try:
                self._shell_conn.close()
            except (OSError, AttributeError):
                pass
            self._shell_conn = None
