import tkinter as tk
from pydo.ydotool.linux import ydotool

from . import _ydo

class TkYdo(_ydo.ydo, ydotool):
    """Use tkinter to track mouse and keys."""
    class Active(_ydo.Active):
        def __init__(self, tool):
            self.tool = tool
            self.r = tool.r

        def __enter__(self):
            self.r.deiconify()
            self.r.attributes('-fullscreen', True, '-topmost', True)
            # TODO: wait for mouse to enter...
            self.tool.click(self.tool.m.LEFT|self.tool.m.DOWN)
            return self
        def __exit__(self):
            self.tool.click(self.tool.m.LEFT|self.tool.m.UP)
            self.r.withdraw()

    def __init__(self, *args, **kwargs):
        super(TkYdo, self).__init__(*args, **kwargs)
        self._active = self.Active(self)

    def active(self):
        return self._active
