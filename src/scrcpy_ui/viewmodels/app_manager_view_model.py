"""ViewModel do painel "Desinstalar apps" do device ativo: lista os apps
instalados pelo usuário (nome + pacote), seleção múltipla, filtro e a
desinstalação (em sequência, com status por app).

Manter ou apagar os dados do app vem das Configurações
(SettingsViewModel.keepAppDataOnUninstall, padrão: apagar).
"""

from __future__ import annotations

import threading
from typing import Callable

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from scrcpy_ui.adb.app_manager import AppInfo, list_user_apps, uninstall_app
from scrcpy_ui.models.app_list_model import AppListModel
from scrcpy_ui.viewmodels.settings_view_model import SettingsViewModel

# Tempo mostrando "Removido" nas linhas antes de recarregar a lista
_REFRESH_AFTER_MS = 1500


class AppManagerViewModel(QObject):
    loadingChanged = Signal()
    errorChanged = Signal()
    selectionChanged = Signal()
    uninstallingChanged = Signal()
    # Resumo de uma rodada de desinstalação (texto, tudo certo?)
    finished = Signal(str, bool)

    _listed = Signal(object, str)  # apps, erro
    _appStatus = Signal(str, str, str)  # pacote, status, mensagem
    _uninstallDone = Signal(int, object)  # removidos, falhas [(app, msg)]

    def __init__(self, serial_provider: Callable[[], str], settings: SettingsViewModel, parent=None):
        super().__init__(parent)
        self._serial_provider = serial_provider
        self._settings = settings
        self._model = AppListModel(self)
        self._loading = False
        self._error = ""
        self._uninstalling = False

        self._listed.connect(self._on_listed)
        self._appStatus.connect(self._on_app_status)
        self._uninstallDone.connect(self._on_uninstall_done)

    # --- Estado ----------------------------------------------------------------

    @Property(QObject, constant=True)
    def appsModel(self) -> AppListModel:
        return self._model

    @Property(bool, notify=loadingChanged)
    def loading(self) -> bool:
        return self._loading

    @Property(str, notify=errorChanged)
    def errorMessage(self) -> str:
        return self._error

    @Property(bool, notify=uninstallingChanged)
    def uninstalling(self) -> bool:
        return self._uninstalling

    @Property(int, notify=selectionChanged)
    def selectedCount(self) -> int:
        return len(self._model.selected_apps())

    @Property("QVariantList", notify=selectionChanged)
    def selectedApps(self) -> list[dict[str, str]]:
        return [{"name": a.name, "package": a.package} for a in self._model.selected_apps()]

    # --- Lista -----------------------------------------------------------------

    @Slot()
    def refresh(self) -> None:
        serial = self._serial_provider()
        if self._loading or not serial:
            return
        self._loading = True
        self.loadingChanged.emit()
        threading.Thread(target=self._list, args=(serial,), daemon=True).start()

    def _list(self, serial: str) -> None:
        try:
            self._listed.emit(list_user_apps(serial), "")
        except Exception as exc:
            self._listed.emit([], str(exc) or exc.__class__.__name__)

    @Slot(object, str)
    def _on_listed(self, apps: list[AppInfo], error: str) -> None:
        self._loading = False
        self.loadingChanged.emit()
        self._error = error
        self.errorChanged.emit()
        if not error:
            self._model.set_apps(apps)
            self.selectionChanged.emit()

    @Slot(str)
    def setFilter(self, text: str) -> None:
        self._model.set_filter(text)

    @Slot(str)
    def toggle(self, package: str) -> None:
        if self._uninstalling:
            return
        self._model.toggle(package)
        self.selectionChanged.emit()

    @Slot()
    def clearSelection(self) -> None:
        self._model.clear_selection()
        self.selectionChanged.emit()

    # --- Desinstalação ---------------------------------------------------------

    @Slot()
    def uninstallSelected(self) -> None:
        serial = self._serial_provider()
        apps = self._model.selected_apps()
        if self._uninstalling or not serial or not apps:
            return
        self._uninstalling = True
        self.uninstallingChanged.emit()
        keep_data = self._settings.keepAppDataOnUninstall
        threading.Thread(target=self._uninstall, args=(serial, apps, keep_data), daemon=True).start()

    def _uninstall(self, serial: str, apps: list[AppInfo], keep_data: bool) -> None:
        removed = 0
        failures: list[tuple[AppInfo, str]] = []
        for app in apps:
            self._appStatus.emit(app.package, "uninstalling", "")
            try:
                uninstall_app(serial, app.package, keep_data)
            except Exception as exc:
                message = str(exc) or exc.__class__.__name__
                failures.append((app, message))
                self._appStatus.emit(app.package, "error", message)
            else:
                removed += 1
                self._appStatus.emit(app.package, "done", "")
        self._uninstallDone.emit(removed, failures)

    @Slot(str, str, str)
    def _on_app_status(self, package: str, status: str, message: str) -> None:
        self._model.set_status(package, status, message)

    @Slot(int, object)
    def _on_uninstall_done(self, removed: int, failures: list) -> None:
        self._uninstalling = False
        self.uninstallingChanged.emit()
        # Os removidos saem da seleção; os que falharam continuam marcados
        self._model.clear_selection()
        for app, _ in failures:
            self._model.toggle(app.package)
        self.selectionChanged.emit()

        if not failures:
            text = "1 app desinstalado" if removed == 1 else f"{removed} apps desinstalados"
            self.finished.emit(text, True)
        else:
            app, message = failures[0]
            self.finished.emit(
                f"{removed} desinstalado(s), {len(failures)} com falha. {app.name}: {message}", False
            )
        # Mostra "Removido" um instante e recarrega (os removidos somem da lista)
        QTimer.singleShot(_REFRESH_AFTER_MS, self.refresh)
