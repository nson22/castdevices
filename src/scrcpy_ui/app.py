"""Bootstrap da aplicação: QGuiApplication + QQmlApplicationEngine."""

from __future__ import annotations

import os
import sys

from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from scrcpy_ui.paths import FONTS_DIR, QML_DIR
from scrcpy_ui.storage.settings_store import SettingsStore
from scrcpy_ui.viewmodels.device_list_view_model import DeviceListViewModel
from scrcpy_ui.viewmodels.device_preview_provider import DevicePreviewProvider
from scrcpy_ui.viewmodels.mirror_view_model import MirrorViewModel
from scrcpy_ui.viewmodels.settings_view_model import SettingsViewModel


def _load_fonts(app: QGuiApplication) -> None:
    roboto_id = QFontDatabase.addApplicationFont(str(FONTS_DIR / "Roboto.ttf"))
    QFontDatabase.addApplicationFont(str(FONTS_DIR / "MaterialIcons-Regular.ttf"))

    roboto_families = QFontDatabase.applicationFontFamilies(roboto_id)
    if roboto_families:
        app.setFont(QFont(roboto_families[0]))


def configure_style() -> None:
    """Material: controles nativos herdam as cores do Theme.qml (via
    Material.theme/accent/background no Main.qml). Variante densa, mais
    adequada a desktop. Precisa rodar antes de criar o QGuiApplication."""
    os.environ.setdefault("QT_QUICK_CONTROLS_MATERIAL_VARIANT", "Dense")
    QQuickStyle.setStyle("Material")


def run() -> int:
    configure_style()
    app = QGuiApplication(sys.argv)
    app.setOrganizationName("scrcpy-ui")
    app.setApplicationName("scrcpy-ui")
    _load_fonts(app)

    preview_provider = DevicePreviewProvider()
    device_list_view_model = DeviceListViewModel(preview_provider)

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
