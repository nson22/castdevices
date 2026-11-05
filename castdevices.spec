# -*- mode: python ; coding: utf-8 -*-
# Build (Windows, macOS ou Linux, sempre no próprio sistema):
#   uv run python packaging/fetch_adb.py      # adb oficial fixado (uma vez)
#   uv run pyinstaller castdevices.spec --noconfirm
# Saída:
#   Windows/Linux: dist/castdevices/  (executável castdevices[.exe] + _internal/)
#   macOS:         dist/CastDevices.app
import sys
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

APP_NAME = "CastDevices"
ICONS = Path("resources/icons")
ADB_DIR = Path("resources/platform-tools")

if not (ADB_DIR / "VERSION").is_file():
    raise SystemExit(
        "adb não encontrado em resources/platform-tools/. "
        "Rode antes: uv run python packaging/fetch_adb.py"
    )

a = Analysis(
    ["packaging/entry.py"],
    pathex=["src"],
    datas=[
        ("src/scrcpy_ui/qml", "scrcpy_ui/qml"),
        ("resources/fonts", "resources/fonts"),
        ("resources/icons", "resources/icons"),
        ("resources/scrcpy-server", "resources/scrcpy-server"),
        # adb oficial fixado (o mesmo do scrcpy) -- ver packaging/fetch_adb.py
        (str(ADB_DIR), "resources/platform-tools"),
        # Licenças (Apache-2.0 do projeto + terceiros; LGPL do Qt/FFmpeg)
        ("LICENSE", "licenses"),
        ("NOTICE", "licenses"),
        ("THIRD_PARTY_NOTICES.md", "licenses"),
        ("LICENSES", "licenses/LICENSES"),
        # Versão do app (importlib.metadata) dentro do executável
        *copy_metadata("castdevices"),
    ],
    hiddenimports=[
        "PySide6.QtQuickControls2",
        "PySide6.QtMultimedia",
    ],
    excludes=[
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtPdf",
        "PySide6.Qt3DCore",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtGraphs",
        "tkinter",
    ],
)

# O hook do QtQml coleta TODOS os módulos QML do PySide6 (inclusive o
# QtWebEngine, ~200 MB). Filtra o que o app não usa -- só Material (+ Basic,
# do qual o Material depende), Layouts, Dialogs e Multimedia ficam.
_UNUSED = (
    "WebEngine", "WebChannel", "WebView", "WebSockets", "Pdf",
    "Quick3D", "Qt63D", "/Qt3D", "Graphs", "Charts", "DataVisualization",
    "Location", "Positioning", "Sensors", "TextToSpeech", "SpatialAudio",
    "VirtualKeyboard", "Scxml", "StateMachine", "RemoteObjects", "Bluetooth",
    "Nfc", "SerialPort", "Qt6Test", "QtTest", "Qt5Compat", "LabsStyleKit",
    "FluentWinUI3", "Imagine", "Universal", "Fusion",
    "Controls2Windows", "Controls/Windows", "/designer", "opengl32sw",
    # adb que o adbutils traz (só Windows): o app usa o de resources/platform-tools
    "adbutils/binaries",
    # Módulos do Qt licenciados só sob GPL (ou comercial), sem opção LGPL: não
    # podem ir num app Apache-2.0. O app não usa nenhum deles.
    "QuickTimeline", "Quick/Timeline", "ShaderTools", "Lottie", "Quick3D",
    "VirtualKeyboard", "Charts", "DataVisualization", "Graphs", "HttpServer",
    "Protobuf", "Grpc", "Mqtt", "Coap", "OpcUa", "WaylandCompositor",
)


_UNUSED_LOWER = tuple(token.lower() for token in _UNUSED)


def _keep(entry):
    # Sem diferenciar maiúsculas: plugins usam nomes minúsculos
    # (ex.: qtvirtualkeyboardplugin, qmldbg_quick3dprofiler)
    dest = entry[0].replace("\\", "/").lower()
    return not any(token in dest for token in _UNUSED_LOWER)


a.binaries = [e for e in a.binaries if _keep(e)]
a.datas = [e for e in a.datas if _keep(e)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="castdevices",
    console=False,
    upx=False,
    icon=str(ICONS / ("castdevices.ico" if sys.platform == "win32" else "castdevices.icns")),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    upx=False,
    name="castdevices",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=str(ICONS / "castdevices.icns"),
        bundle_identifier="io.github.nson22.castdevices",
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "NSHighResolutionCapable": True,
            # Seleção de pasta/arquivo (screenshots, gravações, APK)
            "NSDesktopFolderUsageDescription": "Salvar screenshots e gravações.",
            "NSDocumentsFolderUsageDescription": "Salvar screenshots e gravações.",
            "NSDownloadsFolderUsageDescription": "Escolher APKs para instalar.",
        },
    )
