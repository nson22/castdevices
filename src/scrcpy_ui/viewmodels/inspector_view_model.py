"""ViewModel do inspetor de hierarquia: captura a árvore de elementos da tela
via `uiautomator dump` (leva ~3s, roda em background) e expõe o elemento
selecionado pro QML desenhar o destaque sobre o vídeo.
"""

from __future__ import annotations

import threading

from PySide6.QtCore import Property, QModelIndex, QObject, QRectF, Signal, Slot

from scrcpy_ui.adb import client
from scrcpy_ui.models.ui_hierarchy_model import UiHierarchyModel, UiNode, parse_hierarchy

_REMOTE_DUMP = "/data/local/tmp/scrcpy_ui_dump.xml"

# Ordem em que as propriedades aparecem no painel de detalhes
_DETAIL_KEYS = (
    "text", "content-desc", "resource-id", "class", "package", "bounds",
    "clickable", "long-clickable", "scrollable", "focusable", "enabled",
    "checked", "selected",
)


class InspectorViewModel(QObject):
    busyChanged = Signal()
    errorChanged = Signal()
    hierarchyChanged = Signal()
    selectionChanged = Signal()
    _dumpFinished = Signal(object, int, int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = UiHierarchyModel(self)
        self._busy = False
        self._error = ""
        self._screen_width = 0
        self._screen_height = 0
        self._selected: UiNode | None = None
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

    @Slot(str)
    def refresh(self, serial: str) -> None:
        if self._busy or not serial:
            return
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
        self._error = error
        self.errorChanged.emit()
        if error:
            return
        self._selected = None
        self._screen_width = width
        self._screen_height = height
        self._model.set_roots(roots)
        self.hierarchyChanged.emit()
        self.selectionChanged.emit()

    @Slot(QModelIndex)
    def selectIndex(self, index: QModelIndex) -> None:
        self._selected = self._model.node(index)
        self.selectionChanged.emit()

    @Slot()
    def clearSelection(self) -> None:
        self._selected = None
        self.selectionChanged.emit()
