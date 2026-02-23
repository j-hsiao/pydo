"""YDO implementation using tkinter

Because tk might or might not have the cursor position (if on Xwayland)
a full-screen top-most window must be created to detect the actual
current cursor position.  However, this can be very slow, so for motion,
opt to press a mouse button to force events to fire. moving the mouse
into position.

From observation, while withdrawn, even if focused (because mouse clicked)
events will fire very slowly.  In this case, it is better to only exit
fullscreen and make the current window small so events fire normally.
"""
import tkinter as tk
from pydo.ydotool import ydotool
from pydo.util import tkmove

from . import ydo as _ydo

import sys

class ydo(_ydo.ydo, ydotool):
    """Use tkinter to track mouse and keys."""
    def __init__(self, *args, **kwargs):
        button = kwargs.pop('button', 'MIDDLE')
        movealg = kwargs.pop('move', tkmove.movel1px)
        super(ydo, self).__init__(*args, **kwargs)
        self._state = 0
        self.tk = tk.Tk()
        self._pos = self.tk.winfo_pointerxy()
        self.tk.withdraw()
        _trackname = self.createcommand(self._track_state)
        for item in 'ButtonPress', 'ButtonRelease', 'Enter', 'KeyPress', 'KeyRelease', 'Leave', 'Motion':
            self.tk.call('bind', 'all', '<{}>'.format(item), '{} %X %Y %s'.format(_trackname))
        self._motion_toplevel = tkmove.MotionToplevel(
            self, button, movealg)

    @staticmethod
    def name(func):
        """Return a name for a function."""
        return 'pyfunc_ydo_{}{}'.format(func.__name__, id(func))

    def createcommand(self, f):
        """Bind f to a tcl command and return the name."""
        name = self.name(f)
        self.tk.createcommand(name, f)
        return name

    def _track_state(self, x, y, s):
        """Keep track of position and state bitflags."""
        self._pos = (int(x), int(y))
        self._state = s

    def lockstate(self, key='Caps_Lock'):
        if isinstance(key, str):
            key = self.k(key)
        if key == self.k.Caps_Lock:
            return bool(int(self._state) & 0x02)
        elif key == self.k.Num_Lock:
            return bool(int(self._state) & 0x10)
        else:
            # TODO Scroll lock?
            # but on arch, it seems to do nothing... (LED doesn't even light up)
            return False

    def screensize(self):
        return self.tk.winfo_screenwidth(), self.tk.winfo_screenheight()

    def move(self, x, y, absolute=True):
        self._motion_toplevel.move(x, y, absolute)

    def pos(self):
        return self._pos
