"""Model (QAbstractListModel) puro: só guarda os dados dos devices.

Não conhece adb nem faz nenhuma chamada de rede -- isso é responsabilidade do
DeviceListViewModel. Mantém um "previewRevision" por linha, incrementado pelo
ViewModel sempre que um novo screenshot de preview fica disponível, pra forçar
o QML a reconsultar a imagem (ver DevicePreviewProvider).
"""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt


class DeviceListModel(QAbstractListModel):
    SerialRole = Qt.ItemDataRole.UserRole + 1
    DeviceModelRole = Qt.ItemDataRole.UserRole + 2
    PreviewRevisionRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._devices: list[dict] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._devices)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        device = self._devices[index.row()]
        if role in (Qt.ItemDataRole.DisplayRole, self.SerialRole):
            return device["serial"]
        if role == self.DeviceModelRole:
            return device["deviceModel"]
        if role == self.PreviewRevisionRole:
            return device["previewRevision"]
        return None

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.SerialRole: b"serial",
            self.DeviceModelRole: b"deviceModel",
            self.PreviewRevisionRole: b"previewRevision",
        }

    def set_devices(self, entries: list[dict[str, str]]) -> None:
        previous_revisions = {d["serial"]: d["previewRevision"] for d in self._devices}
        self.beginResetModel()
        self._devices = [
            {
                "serial": entry["serial"],
                "deviceModel": entry["deviceModel"],
                "previewRevision": previous_revisions.get(entry["serial"], 0),
            }
            for entry in entries
        ]
        self.endResetModel()

    def bump_preview_revision(self, serial: str) -> None:
        for row, device in enumerate(self._devices):
            if device["serial"] == serial:
                device["previewRevision"] += 1
                index = self.index(row, 0)
                self.dataChanged.emit(index, index, [self.PreviewRevisionRole])
                return
