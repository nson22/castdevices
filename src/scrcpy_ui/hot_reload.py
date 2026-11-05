"""Hot reload do QML (modo --dev): ao salvar um .qml, recria a engine e a
janela, mantendo posição/tamanho. Os ViewModels vivem no Python e não são
recriados, então uma sessão de espelhamento ativa continua rodando.

Recria a engine inteira (e não só clearComponentCache) porque o Theme é um
singleton QML, e singletons não são descartados pelo cache de componentes.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine

EngineFactory = Callable[[dict | None], QQmlApplicationEngine]


def _print_qt_message(_mode, _context, message: str) -> None:
    print(message, file=sys.stderr, flush=True)


class QmlHotReloader(QObject):
    def __init__(self, create_engine: EngineFactory, qml_dir: Path, parent=None):
        super().__init__(parent)
        self._create_engine = create_engine
        self._qml_dir = qml_dir
        self._engine: QQmlApplicationEngine | None = None
        # Mantém a engine antiga referenciada até o deleteLater rodar -- se o
        # wrapper Python fosse coletado antes, o PySide6 a deletaria na hora,
        # no meio deste slot.
        self._retired: QQmlApplicationEngine | None = None

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(150)
        self._debounce.timeout.connect(self._reload)

        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._debounce.start)
        self._watcher.directoryChanged.connect(self._debounce.start)

    def start(self) -> bool:
        # No Windows, sem console "de verdade" o Qt manda as mensagens (inclusive
        # erros de QML com arquivo:linha) pro canal de debug, não pro terminal.
        qInstallMessageHandler(_print_qt_message)
        self._engine = self._create_engine(None)
        self._watch()
        print(f"[hot reload] observando {self._qml_dir}")
        return bool(self._engine.rootObjects())

    def _watch(self) -> None:
        # Editores que salvam via "escreve num temporário + renomeia" tiram o
        # arquivo do watcher; re-registra tudo a cada reload.
        if self._watcher.files():
            self._watcher.removePaths(self._watcher.files())
        files = [
            str(p) for p in self._qml_dir.iterdir()
            if p.suffix == ".qml" or p.name == "qmldir"
        ]
        self._watcher.addPaths(files)
        if not self._watcher.directories():
            self._watcher.addPath(str(self._qml_dir))

    def _reload(self) -> None:
        self._watch()
        started = time.perf_counter()

        old_window = self._engine.rootObjects()[0] if self._engine.rootObjects() else None
        initial = None
        if old_window is not None:
            initial = {
                "x": old_window.x(),
                "y": old_window.y(),
                "width": old_window.width(),
                "height": old_window.height(),
            }

        new_engine = self._create_engine(initial)
        if not new_engine.rootObjects():
            print("[hot reload] QML com erro -- mantendo a versão anterior (ver erros acima)")
            new_engine.deleteLater()
            return

        if old_window is not None:
            new_engine.rootObjects()[0].setVisibility(old_window.visibility())

        self._retired = self._engine
        self._engine = new_engine
        self._retired.deleteLater()
        print(f"[hot reload] recarregado em {(time.perf_counter() - started) * 1000:.0f} ms")
