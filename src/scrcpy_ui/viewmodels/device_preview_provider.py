"""Screenshots de preview dos devices, servidos pro QML via
"image://devicepreviews/<serial>/<revision>" (a revision na URL só existe pra
forçar o Image do QML a reconsultar quando o preview muda).

O cache (PreviewImageStore) é separado do provider porque a QQmlEngine toma
posse do QQuickImageProvider e o destrói junto com ela -- no hot reload (modo
--dev) a engine é recriada e precisa de um provider novo, mas os previews já
capturados continuam valendo.
"""

from __future__ import annotations

import threading

from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlImageProviderBase
from PySide6.QtQuick import QQuickImageProvider


class PreviewImageStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._images: dict[str, QImage] = {}

    def set_image(self, serial: str, image: QImage) -> None:
        with self._lock:
            self._images[serial] = image

    def get_image(self, serial: str) -> QImage | None:
        with self._lock:
            return self._images.get(serial)


class DevicePreviewProvider(QQuickImageProvider):
    def __init__(self, store: PreviewImageStore):
        super().__init__(QQmlImageProviderBase.ImageType.Image)
        self._store = store

    def requestImage(self, id: str, size, requestedSize):
        image = self._store.get_image(id.split("/", 1)[0])
        if image is None:
            # Transparente: o card mostra o próprio fundo enquanto o preview não chega
            image = QImage(1, 1, QImage.Format.Format_ARGB32)
            image.fill(0)
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image
