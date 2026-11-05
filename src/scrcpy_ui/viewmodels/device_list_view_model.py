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

    def __init__(self, preview_store: PreviewImageStore, parent=None):
        super().__init__(parent)
        self._model = DeviceListModel(self)
        self._preview_store = preview_store
        self.previewReady.connect(self._on_preview_ready)

    @Property(QObject, constant=True)
    def deviceListModel(self) -> DeviceListModel:
        return self._model

    @Slot()
    def refresh(self) -> None:
        devices = client.list_devices()
        entries = []
        for device in devices:
            try:
                model_name = device.prop.model
            except Exception:
                model_name = ""
            entries.append({"serial": device.serial, "deviceModel": model_name})
        self._model.set_devices(entries)

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
