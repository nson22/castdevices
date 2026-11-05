"""ViewModel da tela de listagem: busca os devices via adb, mantém o
DeviceListModel atualizado e captura (em background) um screenshot de preview
por device, publicando no PreviewImageStore.
"""

from __future__ import annotations

import threading

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QImage

from scrcpy_ui.adb import client
from scrcpy_ui.models.device_list_model import DeviceListModel
from scrcpy_ui.viewmodels.device_preview_provider import PreviewImageStore


def _pil_to_qimage(pil_image) -> QImage:
    rgb = pil_image.convert("RGB")
    data = rgb.tobytes("raw", "RGB")
    qimage = QImage(data, rgb.width, rgb.height, QImage.Format.Format_RGB888)
    return qimage.copy()


class DeviceListViewModel(QObject):
    previewReady = Signal(str)
    singleDeviceFound = Signal(str)
    loadingChanged = Signal()
    _listed = Signal(object, object)  # entradas, devices

    def __init__(self, preview_store: PreviewImageStore, parent=None):
        super().__init__(parent)
        self._model = DeviceListModel(self)
        self._preview_store = preview_store
        self._loading = False
        self.previewReady.connect(self._on_preview_ready)
        self._listed.connect(self._on_listed)

    @Property(QObject, constant=True)
    def deviceListModel(self) -> DeviceListModel:
        return self._model

    # Listando devices (a tela mostra o skeleton da grade enquanto isso)
    @Property(bool, notify=loadingChanged)
    def loading(self) -> bool:
        return self._loading

    @Slot()
    def refresh(self) -> None:
        # Listar + ler o modelo de cada device faz chamadas adb (getprop):
        # roda fora da thread da UI pra ela não travar
        if self._loading:
            return
        self._loading = True
        self.loadingChanged.emit()
        threading.Thread(target=self._list, daemon=True).start()

    def _list(self) -> None:
        try:
            devices = client.list_devices()
        except Exception:
            devices = []
        entries = []
        for device in devices:
            try:
                model_name = device.prop.model
            except Exception:
                model_name = ""
            entries.append({"serial": device.serial, "deviceModel": model_name})
        self._listed.emit(entries, devices)

    @Slot(object, object)
    def _on_listed(self, entries: list[dict[str, str]], devices: list) -> None:
        self._model.set_devices(entries)
        self._loading = False
        self.loadingChanged.emit()

        if len(devices) == 1:
            self.singleDeviceFound.emit(devices[0].serial)

        for device in devices:
            threading.Thread(target=self._capture_preview, args=(device,), daemon=True).start()

    def _capture_preview(self, device) -> None:
        try:
            pil_image = device.screenshot()
        except Exception:
            return
        qimage = _pil_to_qimage(pil_image)
        self._preview_store.set_image(device.serial, qimage)
        self.previewReady.emit(device.serial)

    @Slot(str)
    def _on_preview_ready(self, serial: str) -> None:
        self._model.bump_preview_revision(serial)
