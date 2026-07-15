"""全局快捷键 — Win32 RegisterHotKey + QAbstractNativeEventFilter"""

import ctypes
import ctypes.wintypes
from typing import Callable, Optional
from PySide6.QtCore import QAbstractNativeEventFilter, QByteArray
from PySide6.QtWidgets import QWidget


# Win32 constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Key codes for common keys
VK_CODES: dict[str, int] = {
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45, "F": 0x46, "G": 0x47,
    "H": 0x48, "I": 0x49, "J": 0x4A, "K": 0x4B, "L": 0x4C, "M": 0x4D, "N": 0x4E,
    "O": 0x4F, "P": 0x50, "Q": 0x51, "R": 0x52, "S": 0x53, "T": 0x54, "U": 0x55,
    "V": 0x56, "W": 0x57, "X": 0x58, "Y": 0x59, "Z": 0x5A,
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
    "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
    "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "Up": 0x26, "Down": 0x28, "Left": 0x25, "Right": 0x27,
    "Space": 0x20, "Tab": 0x09, "Enter": 0x0D, "Escape": 0x1B,
    "Backspace": 0x08, "Delete": 0x2E, "Insert": 0x2D,
    "Home": 0x24, "End": 0x23, "PageUp": 0x21, "PageDown": 0x22,
    "`": 0xC0, "-": 0xBD, "=": 0xBB, "[": 0xDB, "]": 0xDD,
    "\\": 0xDC, ";": 0xBA, "'": 0xDE, ",": 0xBC, ".": 0xBE, "/": 0xBF,
}

MOD_MAP: dict[str, int] = {
    "Ctrl": MOD_CONTROL, "Control": MOD_CONTROL,
    "Alt": MOD_ALT,
    "Shift": MOD_SHIFT,
    "Win": MOD_WIN, "Windows": MOD_WIN,
}


def parse_hotkey(hotkey_str: str) -> Optional[tuple[int, int]]:
    """解析 'Ctrl,Up' 格式的快捷键字符串，返回 (modifiers, vk_code)"""
    parts = [p.strip() for p in hotkey_str.split(",")]
    if len(parts) < 2:
        return None
    mods = 0
    vk = 0
    for p in parts:
        if p in MOD_MAP:
            mods |= MOD_MAP[p]
        elif p in VK_CODES:
            vk = VK_CODES[p]
    if vk == 0 or mods == 0:
        return None
    return (mods, vk)


class HotkeyManager(QAbstractNativeEventFilter):
    """全局快捷键管理器"""

    def __init__(self, widget: QWidget):
        super().__init__()
        self._widget = widget
        self._callbacks: dict[int, Callable] = {}
        self._next_id = 1
        self._registered: dict[int, tuple[int, int]] = {}  # id -> (mods, vk)

    def register(self, hotkey_str: str, callback: Callable) -> Optional[int]:
        """注册全局快捷键，返回 hotkey_id，失败返回 None"""
        parsed = parse_hotkey(hotkey_str)
        if parsed is None:
            return None
        mods, vk = parsed
        hid = self._next_id
        self._next_id += 1
        hwnd = int(self._widget.winId())
        ok = user32.RegisterHotKey(hwnd, hid, mods, vk)
        if ok:
            self._callbacks[hid] = callback
            self._registered[hid] = (mods, vk)
            return hid
        return None

    def unregister(self, hotkey_id: int):
        """注销快捷键"""
        if hotkey_id in self._registered:
            user32.UnregisterHotKey(int(self._widget.winId()), hotkey_id)
            self._registered.pop(hotkey_id, None)
            self._callbacks.pop(hotkey_id, None)

    def unregister_all(self):
        for hid in list(self._registered.keys()):
            self.unregister(hid)

    def nativeEventFilter(self, event_type: QByteArray, message: int) -> tuple[bool, int]:
        msg = ctypes.wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            hid = msg.wParam
            if hid in self._callbacks:
                self._callbacks[hid]()
                return True, 0
        return False, 0
