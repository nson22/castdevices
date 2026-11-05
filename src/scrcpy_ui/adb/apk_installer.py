"""Instalação de APK num device: envia o arquivo (com progresso real dos bytes
enviados) e roda o `pm install`.

O `pm install` não informa progresso, então essa fase é reportada como um
avanço gradual até quase o fim, só pra a barra não parecer travada.
"""

from __future__ import annotations

import io
import re
import threading
import uuid
from pathlib import Path
from typing import BinaryIO, Callable

from scrcpy_ui.adb import client

# Parte da barra que corresponde ao envio do arquivo; o resto é o pm install
UPLOAD_SHARE = 0.85
_INSTALL_CAP = 0.98
_TICK_SECONDS = 0.2

ProgressCallback = Callable[[float, str], None]  # (0..1, "uploading" | "installing")


class ApkInstallError(RuntimeError):
    pass


class _ProgressReader(io.RawIOBase):
    """Envolve o arquivo e conta os bytes lidos pelo push do adbutils."""

    def __init__(self, raw: BinaryIO, total: int, on_read: Callable[[int, int], None]):
        self._raw = raw
        self._total = max(1, total)
        self._done = 0
        self._on_read = on_read

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> bytes:
        chunk = self._raw.read(size)
        self._done += len(chunk)
        self._on_read(self._done, self._total)
        return chunk

    def readinto(self, buffer) -> int:
        chunk = self.read(len(buffer))
        buffer[: len(chunk)] = chunk
        return len(chunk)


def install_apk(serial: str, apk_path: Path, on_progress: ProgressCallback) -> None:
    """Bloqueante: chame numa thread. Levanta ApkInstallError se falhar."""
    device = client.get_device(serial)
    remote = f"/data/local/tmp/scrcpy_ui_{uuid.uuid4().hex[:8]}.apk"
    total = apk_path.stat().st_size

    on_progress(0.0, "uploading")
    try:
        with apk_path.open("rb") as raw:
            reader = _ProgressReader(
                raw, total, lambda done, size: on_progress(UPLOAD_SHARE * done / size, "uploading")
            )
            device.sync.push(reader, remote)

        on_progress(UPLOAD_SHARE, "installing")
        output = _run_with_ticks(
            lambda: device.shell(["pm", "install", "-r", "-t", remote]),
            lambda value: on_progress(value, "installing"),
        )
    finally:
        try:
            device.shell(["rm", "-f", remote])
        except Exception:
            pass

    if "Success" not in output:
        raise ApkInstallError(_summarize_failure(output))
    on_progress(1.0, "installing")


def _summarize_failure(output: str) -> str:
    """Do texto do pm install (às vezes com stack trace Java), extrai a parte
    útil: "INSTALL_FAILED_..." ou a linha "Error: ..."."""
    match = re.search(r"Failure \[([^\]]+)\]", output)
    if match:
        return match.group(1)
    # Ex.: "java.lang.IllegalArgumentException: Error: Failed to parse APK file: ..."
    match = re.search(r"Error: (.+)", output)
    if match:
        return match.group(1).strip()
    return output.strip().splitlines()[0] if output.strip() else "pm install falhou sem mensagem"


def _run_with_ticks(work: Callable[[], str], tick: Callable[[float], None]) -> str:
    """Roda `work` e, enquanto isso, avança o progresso de UPLOAD_SHARE até
    perto do fim (cada passo cobre 8% do que falta)."""
    result: dict[str, object] = {}

    def target() -> None:
        try:
            result["output"] = work()
        except Exception as exc:
            result["error"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    value = UPLOAD_SHARE
    while thread.is_alive():
        thread.join(_TICK_SECONDS)
        value += (_INSTALL_CAP - value) * 0.08
        tick(value)
    if "error" in result:
        raise ApkInstallError(str(result["error"]))
    return str(result.get("output", ""))
