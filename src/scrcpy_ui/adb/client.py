"""Wrapper fino sobre adbutils para listagem/seleção de devices."""

from __future__ import annotations

import adbutils


def list_devices() -> list[adbutils.AdbDevice]:
    return adbutils.adb.device_list()


def get_device(serial: str) -> adbutils.AdbDevice:
    for device in list_devices():
        if device.serial == serial:
            return device
    raise RuntimeError(f"Device {serial!r} não encontrado (desconectado?)")
