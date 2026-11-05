"""ViewModel da instalação de APK.

- Na grade de devices: o usuário escolhe a APK e confirma; instala em todos os
  devices listados ao mesmo tempo, cada card com a sua barra de progresso.
- No espelhamento: instala só no device ativo; o botão mostra um anel de
  progresso.

O estado por device fica em `installs` (serial -> {progress, phase, message}),
que o QML consulta por `installs[serial]`.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot

from scrcpy_ui.adb.apk_installer import install_apk

# Mínimo de avanço entre duas atualizações enviadas pra UI (evita inundar a
# thread principal com um sinal por bloco enviado)
_MIN_STEP = 0.005
# Depois de tudo terminar, as barras de sucesso somem após esse tempo (erros
# ficam até a próxima instalação)
_CLEAR_DONE_MS = 5000

_RUNNING = ("uploading", "installing")


class ApkInstallViewModel(QObject):
    apkChanged = Signal()
    installsChanged = Signal()
    # Resumo quando um lote termina (texto, sucesso total?)
    finished = Signal(str, bool)
    _progress = Signal(str, float, str)
    _done = Signal(str, str)  # serial, mensagem de erro ("" = sucesso)

    def __init__(self, listed_serials: Callable[[], list[str]], parent=None):
        super().__init__(parent)
        self._listed_serials = listed_serials
        self._apk_path: Path | None = None
        self._installs: dict[str, dict] = {}
        self._batch: list[str] = []
        self._batch_apk = ""

        self._clear_timer = QTimer(self)
        self._clear_timer.setSingleShot(True)
        self._clear_timer.setInterval(_CLEAR_DONE_MS)
        self._clear_timer.timeout.connect(self._clear_done)

        self._progress.connect(self._on_progress)
        self._done.connect(self._on_done)

    # --- APK escolhida -------------------------------------------------------

    @Property(str, notify=apkChanged)
    def apkName(self) -> str:
        return self._apk_path.name if self._apk_path else ""

    @Property(str, notify=apkChanged)
    def apkSize(self) -> str:
        if self._apk_path is None or not self._apk_path.exists():
            return ""
        return f"{self._apk_path.stat().st_size / 1_048_576:.1f} MB"

    @Slot(QUrl)
    def selectApk(self, url: QUrl) -> None:
        path = Path(url.toLocalFile())
        self._apk_path = path if path.is_file() else None
        self.apkChanged.emit()

    @Slot()
    def clearApk(self) -> None:
        self._apk_path = None
        self.apkChanged.emit()

    # --- Estado ----------------------------------------------------------------

    @Property("QVariantMap", notify=installsChanged)
    def installs(self) -> dict[str, dict]:
        return self._installs

    @Property(bool, notify=installsChanged)
    def busy(self) -> bool:
        return any(state["phase"] in _RUNNING for state in self._installs.values())

    @Slot(str, result=bool)
    def isInstalling(self, serial: str) -> bool:
        state = self._installs.get(serial)
        return state is not None and state["phase"] in _RUNNING

    # --- Ações -----------------------------------------------------------------

    @Slot()
    def installOnAll(self) -> None:
        """Grade: instala a APK escolhida em todos os devices listados."""
        self._start(self._listed_serials())

    @Slot(QUrl, str)
    def installFileOn(self, url: QUrl, serial: str) -> None:
        """Espelhamento: escolheu o arquivo -> instala só no device ativo."""
        self.selectApk(url)
        self._start([serial] if serial else [])

    def _start(self, serials: list[str]) -> None:
        if self._apk_path is None or not serials:
            return
        targets = [s for s in serials if not self.isInstalling(s)]
        if not targets:
            return
        self._clear_timer.stop()
        # Nova rodada: limpa resultados antigos (inclusive erros)
        self._installs = {
            s: st for s, st in self._installs.items() if st["phase"] in _RUNNING
        }
        for serial in targets:
            self._installs[serial] = {"progress": 0.0, "phase": "uploading", "message": ""}
        self._batch = targets
        self._batch_apk = self._apk_path.name
        self.installsChanged.emit()

        apk = self._apk_path
        for serial in targets:
            threading.Thread(target=self._install, args=(serial, apk), daemon=True).start()

    def _install(self, serial: str, apk: Path) -> None:
        last = [-1.0]

        def report(value: float, phase: str) -> None:
            if value - last[0] >= _MIN_STEP or value >= 1.0:
                last[0] = value
                self._progress.emit(serial, value, phase)

        try:
            install_apk(serial, apk, report)
        except Exception as exc:
            self._done.emit(serial, str(exc) or exc.__class__.__name__)
        else:
            self._done.emit(serial, "")

    # --- Callbacks na thread principal ----------------------------------------

    @Slot(str, float, str)
    def _on_progress(self, serial: str, value: float, phase: str) -> None:
        state = self._installs.get(serial)
        if state is None or state["phase"] not in _RUNNING:
            return
        state["progress"] = value
        state["phase"] = phase
        self.installsChanged.emit()

    @Slot(str, str)
    def _on_done(self, serial: str, error: str) -> None:
        state = self._installs.get(serial)
        if state is None:
            return
        if error:
            state.update(phase="error", message=error)
        else:
            state.update(phase="done", progress=1.0, message="")
        self.installsChanged.emit()

        if self.busy:
            return
        batch = [self._installs[s] for s in self._batch if s in self._installs]
        failed = [s for s in self._batch if self._installs.get(s, {}).get("phase") == "error"]
        ok = len(batch) - len(failed)
        if not failed:
            target = "1 device" if ok == 1 else f"{ok} devices"
            self.finished.emit(f"{self._batch_apk} instalado em {target}", True)
        else:
            first_error = self._installs[failed[0]]["message"]
            self.finished.emit(
                f"{self._batch_apk}: instalado em {ok} de {len(batch)}. Falhou: {first_error}",
                False,
            )
        self._clear_timer.start()

    def _clear_done(self) -> None:
        self._installs = {s: st for s, st in self._installs.items() if st["phase"] != "done"}
        self.installsChanged.emit()
