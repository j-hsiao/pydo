from pydo.ydotool.windows import ydotool
from . import ydo as _ydo

import ctypes

class _LPoint(ctypes.Structure):
    _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]

class ydo(_ydo.ydo, ydotool):
    @staticmethod
    def lockstate(key='Caps_Lock'):
        if isinstance(key, str):
            key = ydotool.k[key]
        result = ctypes.windll.user32.GetKeyState(key)
        # NOTE: result < 0 implies key is currently pressed down
        # but only interested in the lock state for now...
        return bool(result & 1)

    def screensize(self):
        return self._screensize

    @staticmethod
    def pos():
        result = _LPoint()
        if ctypes.windll.user32.GetCursorPos(ctypes.pointer(result)):
            return result.x, result.y
        else:
            raise OSError('Failed to get cursor position.')
