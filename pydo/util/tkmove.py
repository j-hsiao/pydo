"""Use tk window to monitor mouse position for accurate movement."""
import os
import sys
import textwrap
import time
import tkinter as tk
import textwrap

class ToplevelMotion(object):
    """Use a tk.Toplevel and while loop for accurate mouse motion.

    This fixes an issue where a small mouse movement (due to pointer
    acceleration) might not result in an actual mouse motion.  Using
    callbacks, this sometimes results in no event which means the mouse
    motion cannot continue.  From observation, events don't need to be
    handled for winfo pointerxy to have the newest mouse position.
    """
    def __init__(self, tool, root=None):
        self.tool = tool
        if root is None:
            if getattr(tk, '_default_root', None) is not None:
                root = tk._get_default_root()
        if root is None:
            self.tl = tk.Tk()
            self.tl.configure(bg='black')
        else:
            self.tl = tk.Toplevel(root, bg='black')
        try:
            self.tl.tk.call('package', 'require', 'tkmove')
        except Exception:
            self.tl.tk.eval((
                'lappend auto_path {{{}}}\n'
                'package require tkmove\n'
            ).format(os.path.join(os.path.dirname(__file__), '_tkmove')))
        self.tl.tk.eval(textwrap.dedent(
            '''
            wm withdraw {0}\n
            update
            wm attributes {0} -fullscreen true -topmost true
            wm withdraw {0}
            after 1 {{wm attributes {0} -alpha 0.1}}
            ''').format(self.tl))
        self._mvname = 'relmove_{}'.format(self.tl)
        self._dlname = 'destroyed_{}'.format(self.tl)
        self.tl.tk.createcommand(self._mvname, self._relmove)
        self.tl.tk.createcommand(self._dlname, self._on_destroy)
        self.tl.bind('<Destroy>', self._dlname)

    def _relmove(self, x, y):
        self.tool.move(int(x), int(y), absolute=False)

    def _on_destroy(self):
        self.tl.tk.deletecommand(self._mvname)
        self.tl.tk.deletecommand(self._dlname)

    def destroy(self):
        self.tl.destroy()

    def move(self, x, y, absolute=True, weight=0.5, incr='inf'):
        self.tl.tk.call('::tkmove::wait_deiconify', self.tl)
        if not absolute:
            cx, cy = self.tl.tk.call('winfo', 'pointerxy', self.tl)
            x += cx
            y += cy
        try:
            self.tl.tk.call(
                '::tkmove::move_to', self.tl,
                self._mvname, x, y, '-w', weight, '-m', incr)
        finally:
            self.tl.withdraw()

    def deiconify(self):
        self.tl.tk.call('::tkmove::wait_deiconify', self.tl)
    def withdraw(self):
        self.tl.withdraw()


if __name__ == '__main__':
    from pydo.ydotool import ydotool
    import ast
    with ydotool(daemon=True) as tool:
        motion = ToplevelMotion(tool)
        try:
            response = ' '
            while response:
                if response.strip():
                    x, y = ast.literal_eval(response)
                    motion.move(x, y)
                else:
                    motion.deiconify()
                    print(motion.tl.tk.call('winfo', 'pointerxy', motion.tl))
                    motion.withdraw()
                response = input('>>> ')
        finally:
            motion.destroy()
