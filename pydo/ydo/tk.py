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
from pydo.ydotool.linux import ydotool

from . import _ydo

import sys

class ydo(_ydo.ydo, ydotool):
    """Use tkinter to track mouse and keys."""
    @staticmethod
    def name(func):
        return 'pyfunc_ydo_{}{}'.format(func.__name__, id(func))

    def __init__(self, *args, **kwargs):
        super(TkYdo, self).__init__(*args, **kwargs)
        self.tk = tk.Tk()
        self._state = 0
        self._pos = self.tk.winfo_pointerxy()
        _trackname = self.createcommand(self._track_state)
        for item in 'ButtonPress', 'ButtonRelease', 'Enter', 'KeyPress', 'KeyRelease', 'Leave', 'Motion':
            self.tk.call('bind', 'all', '<{}>'.format(item), '{} %X %Y %s'.format(_trackname))

        self._motion_toplevel = self.MotionToplevel(self)

    class MotionToplevel(object):
        def __init__(self, tool):
            self.variable = tk.BooleanVar(r)
            self.tool = tool
            self.win = tk.Toplevel(r)
            self.win.bindtags(('MotionToplevel'))

        def move(self, x, y):
            """Move mouse to the target x, y position."""
            self.win.geometry('0x0+5+5')
            self.win.attributes('-topmost', True, '-fullscreen', True)
            self.win.deiconify()
            self.win.update()
            self.tool.tk.call('vwait', self.variable)

        def _initiate_motion(self):
            self.tool.click(self.tool.m.MIDDLE|self.tool.m.DOWN)

        def _refine_motion(self, x, y):
            if x == self.tx and y == self.ty:
                self.tool.click(self.tool.m.MIDDLE|self.tool.m.UP)
            else:
                pass

        def _grab_focus(self):
            pass

        def _on_enter(self):
            pass

        def _on_motion(self):
            self.tool.click(self.tool.m.MIDDLE|self.tool.m.DOWN)

        def _finalize(self):
            self.win.withdraw()

    def createcommand(self, f):
        """Bind f to a tcl command and return the name."""
        name = self.name(f)
        self.tk.createcommand(name, f)
        return name

    def _track_state(self, x, y, s):
        self._pos = (int(x), int(y))
        self._state = s

    def lockstate(self, key='Caps_Lock'):
        if isinstance(key, 'Caps_Lock':
            key = self.k(key)
        if key == self.k.Caps_Lock:
            return bool(int(self._state) & 0x02
        elif key == self.k.Num_Lock:
            return bool(int(self._state) & 0x10
        else:
            # TODO Scroll lock?
            # but on arch, it seems to do nothing... (LED doesn't even light up)
            return False

    def screensize(self):
        return self.tk.winfo_screenwidth(), self.tk.winfo_screenheight()

    def move(self, x, y, absolute=True):
        self._motion_toplevel.move(x, y, absolute)
        if not absolute:
            x += self._pos[0]
            y += self._pos[1]
        self._iter = self._move_iter((x, y))
        self.tk.call('vwait', self._reached)

    def pos(self):
        return self._pos

    def _move_iter(self, target):
        try:
            while self._pos != target:
                mv = []
                for i in range(2):
                    if self._pos[i] < target[i]:
                        mv.append(1)
                    elif self._pos[i] > target[i]:
                        mv.append(-1)
                    else:
                        mv.append(0)
                super(TkYdo, self).move(mv[0], mv[1], False)
                yield
        finally:
            if self._pos == target:
                self._iter = None
            else:
                print('motion cancelled?', file=sys.stderr)

    def _on_key(self, key, state):
        self._state = state

    def _on_move(self, x, y, state):
        self._state = state
        self._pos = x, y = (int(x), int(y))
        # TODO: if activating
        if self._iter is not None:
            next(self._iter)
