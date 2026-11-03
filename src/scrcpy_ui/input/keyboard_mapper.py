"""Mapeia Qt.Key para keycodes do Android (android.view.KeyEvent).

Letras e dígitos são calculados por aritmética (A-Z e 0-9 são sequenciais em
ambos os enums); o resto vem de uma tabela pontual de teclas especiais.
"""

from __future__ import annotations

from PySide6.QtCore import Qt

_KEYCODE_A = 29
_KEYCODE_0 = 7

_SPECIAL_KEYS: dict[int, int] = {
    Qt.Key.Key_Up: 19,
    Qt.Key.Key_Down: 20,
    Qt.Key.Key_Left: 21,
    Qt.Key.Key_Right: 22,
    Qt.Key.Key_Comma: 55,
    Qt.Key.Key_Period: 56,
    Qt.Key.Key_Alt: 57,
    Qt.Key.Key_Shift: 59,
    Qt.Key.Key_Tab: 61,
    Qt.Key.Key_Space: 62,
    Qt.Key.Key_Return: 66,
    Qt.Key.Key_Enter: 66,
    Qt.Key.Key_Backspace: 67,
    Qt.Key.Key_QuoteLeft: 68,
    Qt.Key.Key_Minus: 69,
    Qt.Key.Key_Equal: 70,
    Qt.Key.Key_BracketLeft: 71,
    Qt.Key.Key_BracketRight: 72,
    Qt.Key.Key_Backslash: 73,
    Qt.Key.Key_Semicolon: 74,
    Qt.Key.Key_Apostrophe: 75,
    Qt.Key.Key_Slash: 76,
    Qt.Key.Key_PageUp: 92,
    Qt.Key.Key_PageDown: 93,
    Qt.Key.Key_Escape: 111,
    Qt.Key.Key_Delete: 112,
    Qt.Key.Key_Control: 113,
    Qt.Key.Key_Home: 122,
    Qt.Key.Key_End: 123,
}
for _i in range(12):
    _SPECIAL_KEYS[Qt.Key.Key_F1 + _i] = 131 + _i


def qt_key_to_android_keycode(qt_key: int) -> int | None:
    if Qt.Key.Key_A <= qt_key <= Qt.Key.Key_Z:
        return _KEYCODE_A + (qt_key - Qt.Key.Key_A)
    if Qt.Key.Key_0 <= qt_key <= Qt.Key.Key_9:
        return _KEYCODE_0 + (qt_key - Qt.Key.Key_0)
    return _SPECIAL_KEYS.get(qt_key)
