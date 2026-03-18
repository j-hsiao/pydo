"""Use tk window to monitor mouse position for accurate movement."""
import tkinter as tk
import textwrap
import time
import sys

# =================
# motion algorithms
# =================
class MoveAlgorithm(object):
    def __call__(self, tx, ty, absolute):
        target = (tx, ty)
        curpos = yield None
        if not absolute:
            target = (target[0] + curpos[0], target[1] + curpos[1])
        if curpos == target:
            yield None
            return
        delta = self.delta
        try:
            while curpos != target:
                deltas = []
                for i in range(2):
                    delta.append(delta(target[i] - curpos[i]))
                curpos = yield delta
        finally:
            yield None

    def delta(self, dif):
        raise NotImplementedError

class SteppedMove(object):
    def __init__(self, step=5):
        self.step = step
    def delta(self, dif):
        if dif > 0:
            return min(self.step, dif)
        elif dif < 0:
            return max(-self.step, dif)
        else:
            return 0

class WeightedMove(object):
    def __init__(self, weight=0.5):
        self.weight = weight
    def delta(self, dif)
        if dif > 0:
            return max(1, int(dif*self.weight))
        elif dif < 0:
            return min(-1, int(dif*self.weight))
        else:
            return 0


class MotionToplevel_loop(object):
    """Use a tk.Toplevel and while loop for accurate mouse motion.

    This fixes an issue where a small mouse movement (due to pointer
    acceleration) might not result in an actual mouse motion.  Using
    callbacks, this sometimes results in no event which means the mouse
    motion cannot continue.  From observation, events don't need to be
    handled for winfo pointerxy to have the newest mouse position.
    """
    def __init__(self, tool, button='MIDDLE', alg=None):
        if alg is None:
            alg = WeightedMove()
        self._alg = alg

class MotionToplevel_cb(object):
    """Use a tk.Toplevel with callbacks for accurate mouse motion."""
    def __init__(self, tool, button='MIDDLE', alg=None):
        """Motion Toplevel widget.

        tool: a ydo tool.
        """
        if isinstance(button, str):
            button = getattr(tool.m, button)
        if alg is None:
            alg = WeightedMove()
        self.alg = alg
        self._press = button | tool.m.DOWN
        self._release = button | tool.m.UP
        try:
            self.tk = tool.tk
        except AttributeError:
            self.tk = tk.Tk()
        self.tool = tool
        self.variable = tk.BooleanVar(self.tk)
        self.count = tk.IntVar(self.tk)
        self.win = tk.Toplevel(self.tk)
        self.win.bindtags(('MotionToplevel',) + self.win.bindtags())
        self.win.title('TkMouseMove')
        self.win.update()
        self.win.withdraw()
        self.win.update()

        tkbindnum = (tool.m.LEFT, tool.m.MIDDLE, tool.m.RIGHT).index(button)+1
        clickin = tool.createcommand(self._clickin)
        stepcmd = '{} %X %Y'.format(tool.createcommand(self._step))
        self.win.bind(
            '<Enter>',
            'puts "enter: [expr ${0}]"\nif {{${0} == 1 || ${0} == 4}} {{set {0} -1\n{1}\n{2}}}'.format(
                self.count, clickin, stepcmd))
        self.win.bind(
            '<Configure>',
            'if {{${0} >= 0}} {{set {0} [expr ${0}+1]\nputs "configged: [expr ${0}]"}}'.format(self.count))
        self.win.bind(
            '<Motion>',
            'puts "base motion: [expr${0}]"\nif {{${0} >= 0}} {{set {0} -1\n{1}\n{2}}}'.format(self.count, clickin, stepcmd))
        self.win.bind('<B{}-Motion>'.format(tkbindnum), stepcmd)
        # NOTE: moving the window out of the way seems to cause very
        # very slow callback loop on windows, verify on linux?
        # maybe check platform to conditionally add this binding for better visibility?
        # self.win.bind(
        #     '<ButtonPress-{}>'.format(tkbindnum),
        #     textwrap.dedent('''
        #         wm attributes {0} -fullscreen false
        #         wm geometry {0} 200x200+[expr [winfo screenwidth {0}]-200]+[expr [winfo screenheight {0}]-200]
        #         ''').strip().format(self.win))
        pause = tool.createcommand(self._pause)
        self.win.bind('<Escape>', pause)
        self.win.bind('<Destroy>', 'set {} true'.format(self.variable))
        self.win.bind(
            '<space>',
            'if {{"[wm state {0}]" != "withdrawn"}} {{wm withdraw {0}\nupdate}}\n{1}'.format(
                self.win, tool.createcommand(self._resume)))

    def move(self, x, y, absolute=True):
        """Move mouse to the target x, y position (absolute)."""
        self.iter = self.alg(x, y, absolute)
        next(self.iter)
        self._resume()
        self.tk.call('vwait', self.variable)

    def _clickin(self):
        """Click into the window to hold focus."""
        self.tool.click(self._press)

    def _pause(self):
        """Pause motion."""
        self.tool.click(self._release)
        self.win.attributes('-fullscreen', False, '-topmost', False)
        self.win.geometry('200x200+0+0')

    def _resume(self):
        """Resume motion."""
        if self.iter is not None:
            self.count.set(0)
            self.win.geometry('0x0+5+5')
            self.win.attributes('-fullscreen', True, '-topmost', True)
            self.tk.call('after', 'idle', 'wm deiconify {}'.format(self.win))

    def _step(self, x, y, *args):
        """Step towards target mouse position."""
        print('stepping...', x, y, time.time(), *args)
        try:
            cmd = self.iter.send((int(x), int(y)))
        except AttributeError:
            print('_step called but iter was None!', file=sys.stderr)
            if self.iter is None:
                return
            raise
        if cmd is None:
            self.tool.click(self._release)
            self.variable.set(True)
            self.win.withdraw()
            self.iter = None
            return
        print('moving', cmd, time.time())
        self.tool.move_(cmd[0], cmd[1], absolute=False)

    def close(self):
        self.win.destroy()


if __name__ == '__main__':
    from pydo.ydo.tk import ydo
    with ydo(daemon=True) as y:
        try:
            tl = MotionToplevel(y, 'LEFT')
            while coord := input('>>> '):
                x, y = map(int, coord.split(','))

                tl.move(x, y)
        finally:
            tl.close()
