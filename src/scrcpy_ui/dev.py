"""Modo desenvolvimento: `uv run castdevices-dev`.

- .qml salvo -> hot reload na hora (QmlHotReloader, sem reiniciar o app)
- .py salvo  -> o app reinicia sozinho (watchfiles)

O app roda como função (e não como comando "python -m ...") porque no
Windows o subprocesso acharia o Python do sistema antes do .venv.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def _run_app() -> None:
    # Subprocesso do multiprocessing: sem isso o stdout fica em buffer e os
    # avisos de reload/erros de QML só aparecem quando o app fecha.
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    from scrcpy_ui.app import run

    raise SystemExit(run(dev_mode=True))


def main() -> None:
    from watchfiles import PythonFilter, run_process

    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    src = Path(__file__).resolve().parent
    print(f"[dev] .py em {src} reinicia o app; .qml recarrega na hora. Ctrl+C pra sair.", flush=True)
    run_process(src, target=_run_app, watch_filter=PythonFilter())
