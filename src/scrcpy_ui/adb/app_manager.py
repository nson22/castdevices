"""Apps instalados no device: listagem (nome + pacote) e desinstalação.

Nomes: o Android não expõe o nome dos apps pelo `pm`; o scrcpy-server tem a
opção `list_apps`, que usa o PackageManager do device. Ela só lista apps com
ícone no launcher, então a lista final é a de `pm list packages -3` (todos os
apps instalados pelo usuário), com o nome vindo do list_apps quando houver.
Apps do sistema ficam de fora de propósito: desinstalá-los pode quebrar o
device.

Formato do list_apps (marcador "*" = sistema, "-" = usuário; nome longo
quebra e o pacote vem na linha seguinte, só indentado):
     * Calendário                     com.samsung.android.calendar
     - com.zipow.videobox.ZoomApplication
                                      us.zoom.videomeetings
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from scrcpy_ui.adb import client, server_deploy

_LIST_APPS_TIMEOUT = 60


@dataclass(frozen=True)
class AppInfo:
    name: str
    package: str


class UninstallError(RuntimeError):
    pass


def _parse_list_apps(output: str) -> dict[str, str]:
    """pacote -> nome"""
    names: dict[str, str] = {}
    pending_name: str | None = None
    for line in output.splitlines():
        if line.startswith((" * ", " - ")):
            parts = re.split(r"\s{2,}", line[3:].strip())
            if len(parts) >= 2:
                names[parts[-1]] = " ".join(parts[:-1])
                pending_name = None
            else:
                pending_name = parts[0]  # nome longo: pacote na próxima linha
        elif pending_name is not None and line.startswith("   ") and line.strip():
            names[line.strip()] = pending_name
            pending_name = None
    return names


def list_user_apps(serial: str) -> list[AppInfo]:
    device = client.get_device(serial)
    packages = [
        line.removeprefix("package:").strip()
        for line in device.shell(["pm", "list", "packages", "-3"]).splitlines()
        if line.startswith("package:")
    ]
    try:
        server_deploy.ensure_server_pushed(device)
        output = device.shell(
            [
                f"CLASSPATH={server_deploy.SERVER_JAR_REMOTE}",
                "app_process", "/", "com.genymobile.scrcpy.Server", server_deploy.SERVER_VERSION,
                "list_apps=true", "video=false", "audio=false", "control=false",
                # Não remover o jar ao sair: uma sessão de espelhamento pode estar usando
                "cleanup=false",
            ],
            timeout=_LIST_APPS_TIMEOUT,
        )
        names = _parse_list_apps(output)
    except Exception:
        names = {}  # sem nomes: mostra só os pacotes
    apps = [AppInfo(name=names.get(pkg, pkg), package=pkg) for pkg in packages]
    # Apps com nome primeiro (os que o usuário reconhece), depois os só-pacote
    return sorted(apps, key=lambda app: (app.name == app.package, app.name.casefold(), app.package))


def uninstall_app(serial: str, package: str, keep_data: bool) -> None:
    """Bloqueante. keep_data=True mantém os dados e o cache do app no device
    (`pm uninstall -k`); por padrão tudo é apagado."""
    device = client.get_device(serial)
    cmd = ["pm", "uninstall"] + (["-k"] if keep_data else []) + [package]
    output = device.shell(cmd).strip()
    if "Success" not in output:
        # Ex.: "Failure [DELETE_FAILED_INTERNAL_ERROR]"
        match = re.search(r"Failure \[([^\]]+)\]", output)
        raise UninstallError(match.group(1) if match else (output or "pm uninstall falhou"))
