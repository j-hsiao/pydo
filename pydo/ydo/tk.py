import tkinter as tk
from pydo.ydotool.linux import ydotool

from . import _ydo

import sys

class ydo(_ydo.ydo, ydotool):
    """Use tkinter to track mouse and keys."""
    class Active(_ydo.Active):
        def __init__(self, tool):
            self.tool = tool
            r = self.tool.tk

        def __enter__(self):
            r = self.tool.tk
            r.attributes('-fullscreen', True, '-topmost', True)
            self.tool._configs.set(0)
            r.deiconify()
            r.call('vwait', self.tool._ready)
            self.tool.click(self.tool.m.MIDDLE|self.tool.m.DOWN)
            return self

        def __exit__(self):
            self.tool.click(self.tool.m.MIDDLE|self.tool.m.UP)
            self.r.withdraw()

    def __init__(self, *args, **kwargs):
        super(TkYdo, self).__init__(*args, **kwargs)
        self._active = self.Active(self)
        self._iter = None
        self._state = 0
        self.tk = tk.Tk()
        self._pos = self.tk.winfo_pointerxy()

        self._ready = tk.BooleanVar(self.tk)
        self._reached = tk.BooleanVar(self.tk)
        self._configs = tk.IntVar(self.tk)

        # TODO: 
        # From observation:
        #     system  <Motion>    <Configures>    <Configures> on <Enter>
        #     Windows no          1               1
        #     wsl     yes         6               5 (sometimes 6)
        #     X (vnc) no          4               4
        #     wayland yes*        2(sometimes 3)  2 (sometimes 3)
        # *sometimes no... not consistent, not sure how to make it consistent.
        # NOTE: maybe 0x0 is better than 1x1?
        self.tk.createcommand('OnMoveCallback', self._on_move)
        self.tk.createcommand('OnKeyCallback', self._on_key)
        self.tk.bind('<Motion>', 'OnMoveCallback %X %Y %s')
        self.tk.bind('<KeyPress>', 'OnKeyCallback %K %s')
        self.tk.bind(
            '<Enter>',
            'if {{${0} == 1 || ${0} == 4}} {{set {} 1\nset {0} 0}}'.format(self._configs))
        self.tk.bind(
            '<Configure>',
            'set {0} [expr ${0} + 1]'.format(self._configs))


    def lockstate(self, key='Caps_Lock'):
        if isinstance(key, 'Caps_Lock':
            key = self.k(key)
        if key == self.k.Caps_Lock:
            return bool(int(self._state) & 0x02
        elif key == self.k.Num_Lock:
            return bool(int(self._state) & 0x10
        else:
            # TODO Scroll lock?
            # but on arch, it seems to do nothing...
            return False

    def screensize(self):
        return self.tk.winfo_screenwidth(), self.tk.winfo_screenheight()

    def move(self, x, y, absolute=True):
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

    def activate(self):
        return self._active
