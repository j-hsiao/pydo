"""Use tk window to monitor mouse position for accurate movement."""
import tkinter as tk

# =================
# motion algorithms
# =================
# TODO? other algorithms: interpolated motion?
# TODO? guess to reduce the number of steps?
def movel1px(tx, ty):
    """Move 1 pix at a time.

    Yield tuple(click, dx, dy) or None(reached)
    click: True: if click down
           None: if no change
           False: if release
    dx, dy: relative mouse motion to move towards the target.
    """
    target = (tx, ty)
    curpos = yield None
    if curpos == target:
        self.variable.set(True)
        yield None
        return
    step = True
    try:
        while curpos != target:
            delta = [step]
            step = None
            for i in range(2):
                dif = target[i] - curpos[i]
                if dif > 0:
                    delta.append(1)
                elif dif < 0:
                    delta.append(-1)
                else:
                    delta.append(0)
            curpos = yield delta
    finally:
        yield (False, 0, 0)

class MotionToplevel(object):
    def __init__(self, tool, button='MIDDLE', alg=movel1px):
        """Motion Toplevel widget.

        tool: a ydo tool.
        """
        if isinstance(button, str):
            button = getattr(tool.m, button)
        self.alg = alg
        self.press = button | tool.m.DOWN
        self.release = button | tool.m.UP
        try:
            self.tk = tool.tk
        except AttributeError:
            self.tk = tk.Tk()
        self.tool = tool
        self.variable = tk.BooleanVar(self.tool.tk)
        self.count = tk.IntVar(self.tool.tk)
        self.win = tk.Toplevel(r)
        self.win.bindtags(('MotionToplevel',) + self.win.bindtags())
        self.win.withdraw()

        tkbindnum = (tool.m.LEFT, tool.m.MIDDLE, tool.m.RIGHT).index(button)+1
        stepcmd = '{} %X %Y'.forma(tool.createcommand(self._step))
        self.win.bind(
            '<Enter>', 'if {{${0} == 1 || ${0} == 4}} {{{1}}}'.format(self.count, stepcmd))
        self.win.bind('<Motion>', stepcmd)
        self.win.bind('<B{}-Motion>'.format(tkbindnum), stepcmd)
        self.win.bind(
            '<Button-{}>'.format(tkbindnum),
            'wm attributes {0} -fullscreen false\nwm geometry {0} 0x0+0+0'.format(self.win))
        self.win.bind('<Leave>', 'set {} true\nwm withdraw {}'.format(self.variable, self.win))

    def move(self, x, y):
        """Move mouse to the target x, y position (absolute)."""
        self.iter = self.motion1(self, x, y)
        next(self.iter)
        self.win.geometry('0x0+5+5')
        self.win.attributes('-fullscreen', True, '-topmost', True)
        self.win.deiconify()
        self.tool.tk.call('vwait', self.variable)

    def _step(self, x, y):
        cmd = self.iter.send(int(x), int(y))
        if cmd is None:
            self.win.withdraw()
            return
        if cmd[0] is not None:
            if cmd[0]:
                self.tool.click(self.press)
            else:
                self.tool.click(self.release)
                self.win.withdraw()
                return
        self.tool.move_(cmd[1], cmd[2], absolute=False)

