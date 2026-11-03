"""Converte av.VideoFrame (PyAV) em QVideoFrame para alimentar um QVideoSink.

QVideoFrame.bits(plane) retorna um memoryview gravável (confirmado empiricamente
contra o PySide6 instalado); BGRA8888 é usado por simplicidade/correção na
primeira fase (um único plano, sem lidar com stride de planos YUV separados).
"""

from __future__ import annotations

import av
from PySide6.QtCore import QSize
from PySide6.QtMultimedia import QVideoFrame, QVideoFrameFormat


def av_frame_to_qvideoframe(frame: av.VideoFrame) -> QVideoFrame:
    bgra = frame.to_ndarray(format="bgra")

    fmt = QVideoFrameFormat(
        QSize(frame.width, frame.height), QVideoFrameFormat.PixelFormat.Format_BGRA8888
    )
    qframe = QVideoFrame(fmt)
    qframe.map(QVideoFrame.MapMode.WriteOnly)
    try:
        stride = qframe.bytesPerLine(0)
        row_bytes = frame.width * 4
        dst = qframe.bits(0)
        src = bgra.tobytes()
        if stride == row_bytes:
            dst[: len(src)] = src
        else:
            for row in range(frame.height):
                dst_start = row * stride
                src_start = row * row_bytes
                dst[dst_start : dst_start + row_bytes] = src[src_start : src_start + row_bytes]
    finally:
        qframe.unmap()
    return qframe
