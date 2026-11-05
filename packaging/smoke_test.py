"""Smoke test do executável empacotado (roda no CI de cada sistema).

    python packaging/smoke_test.py <executável> <pasta do adb embutido>

1. O adb embutido executa e é a versão fixada.
2. O app abre sem tela (QT_QPA_PLATFORM=offscreen) e continua rodando por
   alguns segundos -- pega import faltando, QML com erro, lib nativa ausente.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ALIVE_SECONDS = 12


def main() -> None:
    exe = Path(sys.argv[1])
    adb_dir = Path(sys.argv[2])

    adb = adb_dir / ("adb.exe" if sys.platform == "win32" else "adb")
    version = subprocess.run([str(adb), "version"], capture_output=True, text=True, timeout=30)
    print(version.stdout.strip())
    if version.returncode != 0 or "Android Debug Bridge" not in version.stdout:
        sys.exit(f"adb embutido não executou: {version.stderr}")

    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_DEBUG_PLUGINS="0")
    log = Path("smoke-test.log")
    with log.open("w") as out:
        proc = subprocess.Popen([str(exe)], stdout=out, stderr=subprocess.STDOUT, env=env)
        try:
            proc.wait(timeout=ALIVE_SECONDS)
        except subprocess.TimeoutExpired:
            print(f"OK: o app continua rodando após {ALIVE_SECONDS}s")
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            return
    print(log.read_text(errors="replace"))
    sys.exit(f"O app fechou sozinho (código {proc.returncode}) -- ver log acima")


if __name__ == "__main__":
    main()
