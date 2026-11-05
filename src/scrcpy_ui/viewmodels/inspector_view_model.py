"""ViewModel do inspetor de hierarquia: captura a árvore de elementos da tela
via `uiautomator dump` (leva ~3s, roda em background) e expõe o elemento
selecionado pro QML desenhar o destaque sobre o vídeo.

Com o painel aberto (`active`), recaptura sozinho quando a tela do device muda:
espera a tela assentar (debounce) e, se mudar de novo durante um dump, agenda
outro ao terminar.
"""

from __future__ import annotations

import threading
from typing import Callable

from PySide6.QtCore import Property, QModelIndex, QObject, QRectF, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication

from scrcpy_ui.adb import client
from scrcpy_ui.models.ui_hierarchy_model import UiHierarchyModel, UiNode, parse_hierarchy

_REMOTE_DUMP = "/data/local/tmp/scrcpy_ui_dump.xml"

# Tempo sem mudanças na tela antes de recapturar. O uiautomator falha com
# "could not get idle state" se a tela ainda estiver animando.
_SETTLE_MS = 800
_AUTO_RETRY_MS = 1500
_MAX_AUTO_RETRIES = 3

# Ordem em que as propriedades aparecem no painel de detalhes
_DETAIL_KEYS = (
    "text", "content-desc", "resource-id", "class", "package", "bounds",
    "clickable", "long-clickable", "scrollable", "focusable", "enabled",
    "checked", "selected",
)
# Atributos que identificam "o mesmo elemento" entre duas capturas
_IDENTITY_KEYS = ("class", "resource-id", "text", "content-desc", "bounds")


def _identity(node: UiNode) -> tuple[str, ...]:
    return tuple(node.attrs.get(key, "") for key in _IDENTITY_KEYS)


def _find(nodes: list[UiNode], identity: tuple[str, ...]) -> UiNode | None:
    for node in nodes:
        if _identity(node) == identity:
            return node
        found = _find(node.children, identity)
        if found is not None:
            return found
    return None


class InspectorViewModel(QObject):
    busyChanged = Signal()
    errorChanged = Signal()
    hierarchyChanged = Signal()
    selectionChanged = Signal()
    activeChanged = Signal()
    _dumpFinished = Signal(object, int, int, str)

    def __init__(self, serial_provider: Callable[[], str], parent=None):
        super().__init__(parent)
        self._serial_provider = serial_provider
        self._model = UiHierarchyModel(self)
        self._busy = False
        self._error = ""
        self._screen_width = 0
        self._screen_height = 0
        self._selected: UiNode | None = None
        self._active = False
        self._auto_pending = False
        self._auto_retries = 0
        self._current_is_auto = False

        self._settle_timer = QTimer(self)
        self._settle_timer.setSingleShot(True)
        self._settle_timer.setInterval(_SETTLE_MS)
        self._settle_timer.timeout.connect(self._auto_refresh)

        self._dumpFinished.connect(self._on_dump_finished)

    @Property(QObject, constant=True)
    def hierarchyModel(self) -> UiHierarchyModel:
        return self._model

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=errorChanged)
    def errorMessage(self) -> str:
        return self._error

    @Property(int, notify=hierarchyChanged)
    def screenWidth(self) -> int:
        return self._screen_width

    @Property(int, notify=hierarchyChanged)
    def screenHeight(self) -> int:
        return self._screen_height

    @Property(bool, notify=selectionChanged)
    def hasSelection(self) -> bool:
        return self._selected is not None

    @Property(QRectF, notify=selectionChanged)
    def selectedBounds(self) -> QRectF:
        if self._selected is None:
            return QRectF()
        return QRectF(*self._selected.bounds)

    @Property("QVariantList", notify=selectionChanged)
    def selectedDetails(self) -> list[dict[str, str]]:
        if self._selected is None:
            return []
        attrs = self._selected.attrs
        return [
            {"name": key, "value": attrs[key]}
            for key in _DETAIL_KEYS
            if attrs.get(key)
        ]

    def _get_active(self) -> bool:
        return self._active

    def _set_active(self, value: bool) -> None:
        if value == self._active:
            return
        self._active = value
        if value:
            self.refresh()
        else:
            self._settle_timer.stop()
            self._auto_pending = False
            self.clearSelection()
        self.activeChanged.emit()

    # Painel aberto: captura ao abrir e recaptura quando a tela mudar
    active = Property(bool, _get_active, _set_active, notify=activeChanged)

    @Slot()
    def notifyScreenChanged(self) -> None:
        if self._active:
            self._auto_retries = 0
            self._settle_timer.start()  # reinicia: só dispara com a tela parada

    def _auto_refresh(self) -> None:
        if not self._active:
            return
        if self._busy:
            self._auto_pending = True
            return
        self._start_dump(auto=True)

    @Slot()
    def refresh(self) -> None:
        if self._busy:
            return
        self._settle_timer.stop()
        self._auto_retries = 0
        self._start_dump(auto=False)

    def _start_dump(self, auto: bool) -> None:
        serial = self._serial_provider()
        if not serial:
            return
        self._current_is_auto = auto
        self._auto_pending = False
        self._busy = True
        self.busyChanged.emit()
        threading.Thread(target=self._dump, args=(serial,), daemon=True).start()

    def _dump(self, serial: str) -> None:
        try:
            device = client.get_device(serial)
            output = device.shell(f"uiautomator dump {_REMOTE_DUMP}")
            if "dumped to" not in output:
                # Ex.: "ERROR: could not get idle state." com a tela animando
                raise RuntimeError(output.strip() or "uiautomator dump falhou")
            roots, rotation = parse_hierarchy(device.shell(f"cat {_REMOTE_DUMP}"))
            size = device.window_size(landscape=rotation in (1, 3))
            self._dumpFinished.emit(roots, size.width, size.height, "")
        except Exception as exc:
            self._dumpFinished.emit([], 0, 0, str(exc))

    @Slot(object, int, int, str)
    def _on_dump_finished(self, roots: list[UiNode], width: int, height: int, error: str) -> None:
        self._busy = False
        self.busyChanged.emit()

        if error and self._current_is_auto and self._model.rowCount() > 0:
            # Falha numa recaptura automática (tela ainda animando): mantém a
            # árvore anterior sem mostrar erro e tenta de novo daqui a pouco.
            if self._active and self._auto_retries < _MAX_AUTO_RETRIES:
                self._auto_retries += 1
                self._settle_timer.start(_AUTO_RETRY_MS)
            return

        self._error = error
        self.errorChanged.emit()
        if not error:
            self._apply_hierarchy(roots, width, height)

        if self._auto_pending and self._active:
            # A tela mudou durante o dump: o resultado já pode estar velho
            self._settle_timer.start(_SETTLE_MS)

    def _apply_hierarchy(self, roots: list[UiNode], width: int, height: int) -> None:
        previous = _identity(self._selected) if self._selected is not None else None
        self._screen_width = width
        self._screen_height = height
        self._model.set_roots(roots)
        self._selected = _find(roots, previous) if previous is not None else None
        self.hierarchyChanged.emit()
        self.selectionChanged.emit()

    @Slot(result=QModelIndex)
    def selectedIndex(self) -> QModelIndex:
        """Índice do elemento selecionado no modelo atual (pra restaurar a
        seleção do TreeView depois de uma recaptura)."""
        node = self._selected
        if node is None:
            return QModelIndex()
        return self._model.createIndex(node.row, 0, node)

    @Slot(str, str, result=str)
    def copyValueFor(self, name: str, value: str) -> str:
        """Valor que o botão de copiar de uma propriedade vai copiar (o QML usa
        no tooltip)."""
        if name == "resource-id":
            # "com.app:id/botao_ok" -> "botao_ok"
            return value.rsplit("/", 1)[-1]
        return value

    @Slot(str, str)
    def copyDetail(self, name: str, value: str) -> None:
        QGuiApplication.clipboard().setText(self.copyValueFor(name, value))

    @Slot(QModelIndex)
    def selectIndex(self, index: QModelIndex) -> None:
        self._selected = self._model.node(index)
        self.selectionChanged.emit()

    @Slot()
    def clearSelection(self) -> None:
        self._selected = None
        self.selectionChanged.emit()
