"""Push do scrcpy-server.jar e inicialização do processo do server no device.

O scrcpy-server faz self-cleanup por padrão ao detectar que a conexão caiu
(remove o próprio jar de /data/local/tmp/), então o jar precisa ser (re)garantido
antes de cada sessão, não só na primeira vez.
"""

from __future__ import annotations

import adbutils

from scrcpy_ui.paths import SERVER_DIR

SERVER_JAR_LOCAL = SERVER_DIR / "scrcpy-server-v4.0.jar"
SERVER_JAR_REMOTE = "/data/local/tmp/scrcpy-server.jar"
SERVER_VERSION = "4.0"


def ensure_server_pushed(device: adbutils.AdbDevice) -> None:
    local_size = SERVER_JAR_LOCAL.stat().st_size
    try:
        info = device.sync.stat(SERVER_JAR_REMOTE)
        if info.size == local_size:
            return
    except Exception:
        pass
    device.sync.push(str(SERVER_JAR_LOCAL), SERVER_JAR_REMOTE, mode=0o644)


def socket_name_for(scid: int) -> str:
    return f"scrcpy_{scid:08x}"


def start_server(
    device: adbutils.AdbDevice,
    scid: int,
    *,
    video: bool = True,
    video_codec: str = "h264",
    max_size: int = 0,
    video_bit_rate: int = 0,
    max_fps: int = 0,
    audio: bool = False,
    audio_codec: str = "opus",
    control: bool = True,
    stay_awake: bool = False,
    show_touches: bool = False,
) -> adbutils.AdbConnection:
    cmd = [
        f"CLASSPATH={SERVER_JAR_REMOTE}",
        "app_process",
        "/",
        "com.genymobile.scrcpy.Server",
        SERVER_VERSION,
        f"scid={scid:08x}",
        f"video={'true' if video else 'false'}",
        f"audio={'true' if audio else 'false'}",
        f"control={'true' if control else 'false'}",
    ]
    if video:
        if video_codec != "h264":
            cmd.append(f"video_codec={video_codec}")
        if max_size:
            cmd.append(f"max_size={max_size}")
        if video_bit_rate:
            cmd.append(f"video_bit_rate={video_bit_rate}")
        if max_fps:
            cmd.append(f"max_fps={max_fps}")
    if audio:
        cmd.append(f"audio_codec={audio_codec}")
    if stay_awake:
        cmd.append("stay_awake=true")
    if show_touches:
        cmd.append("show_touches=true")
    return device.shell(cmd, stream=True)
