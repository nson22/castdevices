"""Lista de apps instalados (nome + pacote) com seleção e status de
desinstalação por app, filtrável por texto (nome ou pacote)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from scrcpy_ui.adb.app_manager import AppInfo


class AppListModel(QAbstractListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    PackageRole = Qt.ItemDataRole.UserRole + 2
    SelectedRole = Qt.ItemDataRole.UserRole + 3
    # "" | "uninstalling" | "done" | "error"
    StatusRole = Qt.ItemDataRole.UserRole + 4
    MessageRole = Qt.ItemDataRole.UserRole + 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._apps: list[AppInfo] = []
        self._visible: list[AppInfo] = []
        self._filter = ""
        self._selected: set[str] = set()
        self._status: dict[str, tuple[str, str]] = {}

    # --- QAbstractListModel ----------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._visible)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        app = self._visible[index.row()]
        if role in (Qt.ItemDataRole.DisplayRole, self.NameRole):
            return app.name
        if role == self.PackageRole:
            return app.package
        if role == self.SelectedRole:
            return app.package in self._selected
        if role == self.StatusRole:
            return self._status.get(app.package, ("", ""))[0]
        if role == self.MessageRole:
            return self._status.get(app.package, ("", ""))[1]
        return None

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.NameRole: b"appName",
            self.PackageRole: b"packageName",
            self.SelectedRole: b"selected",
            self.StatusRole: b"status",
            self.MessageRole: b"message",
        }

    # --- Operações -------------------------------------------------------------

    def set_apps(self, apps: list[AppInfo]) -> None:
        packages = {app.package for app in apps}
        self.beginResetModel()
        self._apps = apps
        self._selected &= packages  # some o que não existe mais
        self._status = {p: s for p, s in self._status.items() if p in packages}
        self._apply_filter()
        self.endResetModel()

    def set_filter(self, text: str) -> None:
        self.beginResetModel()
        self._filter = text.strip().casefold()
        self._apply_filter()
        self.endResetModel()

    def _apply_filter(self) -> None:
        f = self._filter
        self._visible = [
            app for app in self._apps
            if not f or f in app.name.casefold() or f in app.package.casefold()
        ]

    def toggle(self, package: str) -> None:
        if package in self._selected:
            self._selected.discard(package)
        else:
            self._selected.add(package)
        self._emit_changed(package, [self.SelectedRole])

    def clear_selection(self) -> None:
        changed = list(self._selected)
        self._selected.clear()
        for package in changed:
            self._emit_changed(package, [self.SelectedRole])

    def selected_apps(self) -> list[AppInfo]:
        return [app for app in self._apps if app.package in self._selected]

    def set_status(self, package: str, status: str, message: str = "") -> None:
        if status:
            self._status[package] = (status, message)
        else:
            self._status.pop(package, None)
        self._emit_changed(package, [self.StatusRole, self.MessageRole])

    def _emit_changed(self, package: str, roles: list[int]) -> None:
        for row, app in enumerate(self._visible):
            if app.package == package:
                index = self.index(row, 0)
                self.dataChanged.emit(index, index, roles)
                return
