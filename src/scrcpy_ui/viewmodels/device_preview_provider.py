"""QQuickImageProvider que serve os screenshots capturados dos devices.

Fica entre o DeviceListViewModel (quem captura/atualiza as imagens) e o QML
(que pede "image://devicepreviews/<serial>/<revision>" -- a revision na URL
só existe pra forçar o Image do QML a reconsultar quando o preview muda).
"""

from __future__ import annotations

import threading

from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlImageProviderBase
from PySide6.QtQuick import QQuickImageProvider


class DevicePreviewProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQmlImageProviderBase.ImageType.Image)
        self._lock = threading.Lock()
        self._images: dict[str, QImage] = {}

    def set_image(self, serial: str, image: QImage) -> None:
        with self._lock:
            self._images[serial] = image

    def requestImage(self, id: str, size, requestedSize):
        serial = id.split("/", 1)[0]
        with self._lock:
            image = self._images.get(serial)
        if image is None:
            image = QImage(1, 1, QImage.Format.Format_RGB32)
            image.fill(0x202124)
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image
