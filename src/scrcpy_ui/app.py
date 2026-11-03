"""Bootstrap da aplicação: QGuiApplication + QQmlApplicationEngine."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from scrcpy_ui.storage.settings_store import SettingsStore
from scrcpy_ui.viewmodels.device_list_view_model import DeviceListViewModel
from scrcpy_ui.viewmodels.device_preview_provider import DevicePreviewProvider
from scrcpy_ui.viewmodels.mirror_view_model import MirrorViewModel
from scrcpy_ui.viewmodels.settings_view_model import SettingsViewModel

QML_DIR = Path(__file__).resolve().parent / "qml"
FONTS_DIR = Path(__file__).resolve().parents[2] / "resources" / "fonts"


def _load_fonts(app: QGuiApplication) -> None:
    roboto_id = QFontDatabase.addApplicationFont(str(FONTS_DIR / "Roboto.ttf"))
    QFontDatabase.addApplicationFont(str(FONTS_DIR / "MaterialIcons-Regular.ttf"))

    roboto_families = QFontDatabase.applicationFontFamilies(roboto_id)
    if roboto_families:
        app.setFont(QFont(roboto_families[0]))


def run() -> int:
    app = QGuiApplication(sys.argv)
    app.setOrganizationName("scrcpy-ui")
    app.setApplicationName("scrcpy-ui")
    _load_fonts(app)

    preview_provider = DevicePreviewProvider()
    device_list_view_model = DeviceListViewModel(preview_provider)
    device_list_view_model.refresh()

    settings_store = SettingsStore()
    settings_view_model = SettingsViewModel(settings_store)
    mirror_view_model = MirrorViewModel(settings_view_model)

    engine = QQmlApplicationEngine()
    engine.addImageProvider("devicepreviews", preview_provider)
    engine.rootContext().setContextProperty("deviceListViewModel", device_list_view_model)
    engine.rootContext().setContextProperty("mirrorViewModel", mirror_view_model)
    engine.rootContext().setContextProperty("settingsViewModel", settings_view_model)
    engine.load(str(QML_DIR / "Main.qml"))

    if not engine.rootObjects():
        return -1

    return app.exec()
