"""Árvore de elementos da tela do device (saída do `uiautomator dump`),
exposta pro TreeView do QML."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt

_BOUNDS_RE = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")


class UiNode:
    __slots__ = ("attrs", "parent", "children", "row")

    def __init__(self, attrs: dict[str, str], parent: UiNode | None, row: int):
        self.attrs = attrs
        self.parent = parent
        self.children: list[UiNode] = []
        self.row = row

    @property
    def label(self) -> str:
        cls = self.attrs.get("class", "").rsplit(".", 1)[-1] or "node"
        text = self.attrs.get("text", "")
        desc = self.attrs.get("content-desc", "")
        res_id = self.attrs.get("resource-id", "").split(":id/", 1)[-1]
        if text:
            return f'{cls}  "{text}"'
        if desc:
            return f"{cls}  [{desc}]"
        if res_id:
            return f"{cls}  #{res_id}"
        return cls

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        """(x, y, largura, altura) em pixels físicos da tela do device."""
        match = _BOUNDS_RE.fullmatch(self.attrs.get("bounds", ""))
        if not match:
            return (0, 0, 0, 0)
        x1, y1, x2, y2 = map(int, match.groups())
        return (x1, y1, x2 - x1, y2 - y1)


def parse_hierarchy(xml: str) -> tuple[list[UiNode], int]:
    """Retorna (nós raiz, rotação da tela 0-3)."""
    root = ET.fromstring(xml)

    def build(element: ET.Element, parent: UiNode | None, row: int) -> UiNode:
        node = UiNode(dict(element.attrib), parent, row)
        node.children = [
            build(child, node, i) for i, child in enumerate(element.findall("node"))
        ]
        return node

    roots = [build(el, None, i) for i, el in enumerate(root.findall("node"))]
    return roots, int(root.get("rotation", "0") or 0)


class UiHierarchyModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._roots: list[UiNode] = []

    def set_roots(self, roots: list[UiNode]) -> None:
        self.beginResetModel()
        self._roots = roots
        self.endResetModel()

    def node(self, index: QModelIndex) -> UiNode | None:
        return index.internalPointer() if index.isValid() else None

    def _children(self, parent: QModelIndex) -> list[UiNode]:
        return parent.internalPointer().children if parent.isValid() else self._roots

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        siblings = self._children(parent)
        if column != 0 or not 0 <= row < len(siblings):
            return QModelIndex()
        return self.createIndex(row, 0, siblings[row])

    def parent(self, index: QModelIndex = QModelIndex()) -> QModelIndex:
        node = self.node(index)
        if node is None or node.parent is None:
            return QModelIndex()
        return self.createIndex(node.parent.row, 0, node.parent)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.column() > 0:
            return 0
        return len(self._children(parent))

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        node = self.node(index)
        if node is not None and role == Qt.ItemDataRole.DisplayRole:
            return node.label
        return None
