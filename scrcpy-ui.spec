# -*- mode: python ; coding: utf-8 -*-
# Build: uv run pyinstaller scrcpy-ui.spec --noconfirm
# Saída: dist/scrcpy-ui/scrcpy-ui.exe (+ DLLs/recursos na mesma pasta)
from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ["packaging/entry.py"],
    pathex=["src"],
    datas=[
        ("src/scrcpy_ui/qml", "scrcpy_ui/qml"),
        ("resources/fonts", "resources/fonts"),
        ("resources/scrcpy-server", "resources/scrcpy-server"),
        # adb.exe + AdbWinApi.dll que o adbutils traz embutidos
        *collect_data_files("adbutils"),
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
)


def _keep(entry):
    dest = entry[0].replace("\\", "/")
    return not any(token in dest for token in _UNUSED)


a.binaries = [e for e in a.binaries if _keep(e)]
a.datas = [e for e in a.datas if _keep(e)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="scrcpy-ui",
    console=False,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    upx=False,
    name="scrcpy-ui",
)
