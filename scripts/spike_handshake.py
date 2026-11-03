"""Spike: valida o handshake/protocolo scrcpy (v4.0) contra um device real.

Confirma empiricamente, antes de implementar o parser definitivo em
`src/scrcpy_ui/protocol/`, que o entendimento do protocolo (lido do código-fonte
oficial do scrcpy tag v4.0) bate com o que o scrcpy-server.jar bundlado realmente
envia: nome do device (64 bytes), codec id, cabecalho de sessao de video (12 bytes)
e o framing de pacotes (header de 12 bytes + payload).

Uso: uv run python scripts/spike_handshake.py
"""

from __future__ import annotations

import random
import socket
import struct
import sys
import threading
from pathlib import Path

import adbutils

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER_JAR_LOCAL = PROJECT_ROOT / "resources" / "scrcpy-server" / "scrcpy-server-v4.0.jar"
SERVER_JAR_REMOTE = "/data/local/tmp/scrcpy-server.jar"
SERVER_VERSION = "4.0"
DEVICE_NAME_FIELD_LENGTH = 64


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError(f"socket fechado lendo (tinha {len(buf)}/{n} bytes)")
        buf += chunk
    return bytes(buf)


def ensure_server_pushed(device: adbutils.AdbDevice) -> None:
    local_size = SERVER_JAR_LOCAL.stat().st_size
    try:
        info = device.sync.stat(SERVER_JAR_REMOTE)
        if info.size == local_size:
            print(f"[*] scrcpy-server.jar já presente no device ({info.size} bytes), pulando push")
            return
    except Exception:
        pass
    print(f"[*] enviando {SERVER_JAR_LOCAL.name} ({local_size} bytes) para {SERVER_JAR_REMOTE}")
    device.sync.push(str(SERVER_JAR_LOCAL), SERVER_JAR_REMOTE, mode=0o644)


def main() -> None:
    devices = adbutils.adb.device_list()
    if not devices:
        print("Nenhum device conectado (adb devices).")
        sys.exit(1)
    device = devices[0]
    print(f"[*] usando device {device.serial}")

    ensure_server_pushed(device)

    scid = random.getrandbits(31)
    socket_name = f"scrcpy_{scid:08x}"
    print(f"[*] scid={scid:08x} socket_name={socket_name}")

    local_srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_srv.bind(("127.0.0.1", 0))
    local_srv.listen(2)
    local_port = local_srv.getsockname()[1]
    print(f"[*] ouvindo localmente em 127.0.0.1:{local_port}")

    device.reverse(f"localabstract:{socket_name}", f"tcp:{local_port}")
    print("[*] adb reverse configurado")

    cmd = [
        f"CLASSPATH={SERVER_JAR_REMOTE}",
        "app_process",
        "/",
        "com.genymobile.scrcpy.Server",
        SERVER_VERSION,
        f"scid={scid:08x}",
        "video=true",
        "audio=false",
        "control=true",
        "log_level=verbose",
    ]
    print(f"[*] iniciando server: {' '.join(cmd)}")
    shell_conn = device.shell(cmd, stream=True)

    def drain_server_output() -> None:
        try:
            while True:
                data = shell_conn.conn.recv(4096)
                if not data:
                    break
                sys.stdout.write("[server] " + data.decode(errors="replace"))
                sys.stdout.flush()
        except OSError:
            pass

    threading.Thread(target=drain_server_output, daemon=True).start()

    local_srv.settimeout(10)
    try:
        print("[*] aguardando conexão do video socket...")
        video_sock, _ = local_srv.accept()
        print("[+] video socket conectado")

        print("[*] aguardando conexão do control socket...")
        control_sock, _ = local_srv.accept()
        print("[+] control socket conectado")
    finally:
        device.reverse_remove(f"localabstract:{socket_name}")
        print("[*] adb reverse removido (tunnel não é mais necessário)")

    name_buf = recv_exact(video_sock, DEVICE_NAME_FIELD_LENGTH)
    device_name = name_buf.split(b"\0", 1)[0].decode("utf-8", errors="replace")
    print(f"[+] device_name = {device_name!r}")

    codec_id_bytes = recv_exact(video_sock, 4)
    codec_id = struct.unpack(">I", codec_id_bytes)[0]
    print(f"[+] codec_id = 0x{codec_id:08x} ({codec_id_bytes!r})")

    header = recv_exact(video_sock, 12)
    is_session = bool(header[0] & 0x80)
    client_resized = bool(header[3] & 1)
    width, height = struct.unpack(">II", header[4:12])
    print(f"[+] session header: is_session={is_session} client_resized={client_resized} "
          f"width={width} height={height}")

    for i in range(5):
        pkt_header = recv_exact(video_sock, 12)
        pts_flags = struct.unpack(">Q", pkt_header[0:8])[0]
        length = struct.unpack(">I", pkt_header[8:12])[0]
        is_config = bool(pts_flags & (1 << 62))
        is_key = bool(pts_flags & (1 << 61))
        pts = pts_flags & ((1 << 61) - 1)
        payload = recv_exact(video_sock, length)
        print(f"[+] packet {i}: len={length} config={is_config} key={is_key} pts={pts} "
              f"first_bytes={payload[:8].hex()}")

    print("[*] spike concluído com sucesso, encerrando")
    video_sock.close()
    control_sock.close()
    shell_conn.close()


if __name__ == "__main__":
    main()
