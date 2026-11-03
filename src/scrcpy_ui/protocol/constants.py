"""Constantes do protocolo de socket do scrcpy (validadas contra scrcpy-server v4.0).

Valores confirmados lendo o código-fonte oficial (app/src/*.c, tag v4.0) e validados
empiricamente com um device real (ver scripts/spike_handshake.py).
"""

from __future__ import annotations

from enum import IntEnum

DEVICE_NAME_FIELD_LENGTH = 64
CODEC_ID_H264 = 0x68323634  # b"h264"

PACKET_HEADER_SIZE = 12
PACKET_FLAG_CONFIG = 1 << 62
PACKET_FLAG_KEY_FRAME = 1 << 61
PACKET_PTS_MASK = (1 << 61) - 1

POINTER_ID_MOUSE = 0xFFFFFFFFFFFFFFFF


class ControlMsgType(IntEnum):
    INJECT_KEYCODE = 0
    INJECT_TEXT = 1
    INJECT_TOUCH_EVENT = 2
    INJECT_SCROLL_EVENT = 3
    BACK_OR_SCREEN_ON = 4
    EXPAND_NOTIFICATION_PANEL = 5
    EXPAND_SETTINGS_PANEL = 6
    COLLAPSE_PANELS = 7
    GET_CLIPBOARD = 8
    SET_CLIPBOARD = 9
    SET_DISPLAY_POWER = 10
    ROTATE_DEVICE = 11
    UHID_CREATE = 12
    UHID_INPUT = 13
    UHID_DESTROY = 14
    OPEN_HARD_KEYBOARD_SETTINGS = 15
    START_APP = 16
    RESET_VIDEO = 17
    CAMERA_SET_TORCH = 18
    CAMERA_ZOOM_IN = 19
    CAMERA_ZOOM_OUT = 20
    RESIZE_DISPLAY = 21


class DeviceMsgType(IntEnum):
    CLIPBOARD = 0
    ACK_CLIPBOARD = 1
    UHID_OUTPUT = 2


class MotionEventAction(IntEnum):
    DOWN = 0
    UP = 1
    MOVE = 2
    CANCEL = 3


class MotionEventButton(IntEnum):
    PRIMARY = 1 << 0
    SECONDARY = 1 << 1
    TERTIARY = 1 << 2


class KeyEventAction(IntEnum):
    DOWN = 0
    UP = 1
