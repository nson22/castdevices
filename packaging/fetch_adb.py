"""Baixa o adb oficial (Android platform-tools) para empacotar junto do app,
como o scrcpy faz nos releases dele (app/deps/adb_*.sh): versão fixada e
conferência de SHA-256 antes de extrair.

    uv run python packaging/fetch_adb.py [windows|macos|linux]

Sem argumento, usa o sistema atual. Extrai só o necessário para
resources/platform-tools/ (fora do git; ver .gitignore):
- Windows: adb.exe, AdbWinApi.dll, AdbWinUsbApi.dll
- macOS/Linux: adb
- sempre: NOTICE.txt (licenças do platform-tools, redistribuído junto)
"""

from __future__ import annotations

import hashlib
import shutil
import stat
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

# Mesma versão e hashes do scrcpy v4.0 (app/deps/adb_{windows,macos,linux}.sh)
VERSION = "37.0.0"
PLATFORMS = {
    "windows": (
        "win",
        "4fe305812db074cea32903a489d061eb4454cbc90a49e8fea677f4b7af764918",
        ["adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll"],
    ),
    "macos": (
        "darwin",
        "094a1395683c509fd4d48667da0d8b5ef4d42b2abfcd29f2e8149e2f989357c7",
        ["adb"],
    ),
    "linux": (
        "linux",
        "198ae156ab285fa555987219af237b31102fefe8b9d2bc274708a8d4f2865a07",
        ["adb"],
    ),
}
DEST = Path(__file__).resolve().parents[1] / "resources" / "platform-tools"


def current_platform() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def main() -> None:
    platform = sys.argv[1] if len(sys.argv) > 1 else current_platform()
    suffix, sha256, files = PLATFORMS[platform]
    url = f"https://dl.google.com/android/repository/platform-tools_r{VERSION}-{suffix}.zip"

    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "platform-tools.zip"
        print(f"Baixando {url}")
        with urllib.request.urlopen(url, timeout=120) as response, archive.open("wb") as out:
            shutil.copyfileobj(response, out)

        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != sha256:
            sys.exit(f"SHA-256 não confere!\n  esperado: {sha256}\n  obtido:   {digest}")
        print(f"SHA-256 ok ({digest})")

        if DEST.exists():
            shutil.rmtree(DEST)
        DEST.mkdir(parents=True)
        with zipfile.ZipFile(archive) as zf:
            for name in files:
                target = DEST / name
                with zf.open(f"platform-tools/{name}") as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                if name == "adb":
                    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                print(f"  {target.relative_to(DEST.parents[1])}")

        # Licenças do platform-tools: vão junto do adb no pacote
        with zipfile.ZipFile(archive) as zf:
            with zf.open("platform-tools/NOTICE.txt") as src, (DEST / "NOTICE.txt").open("wb") as dst:
                shutil.copyfileobj(src, dst)
        print(f"  {(DEST / 'NOTICE.txt').relative_to(DEST.parents[1])}")

    (DEST / "VERSION").write_text(f"platform-tools {VERSION} ({platform})\n", encoding="utf-8")
    print(f"adb {VERSION} pronto em {DEST}")


if __name__ == "__main__":
    main()
