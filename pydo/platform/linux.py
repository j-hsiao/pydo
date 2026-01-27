"""

Notes on sudo:
    It seems like sudo defaults to reading password from the terminal.
    This means there is no special handling required for sudo password.
    Once the process is started, then there's no need for anymore sudo.
"""
from collections import defaultdict, deque
import codecs
import io
import itertools
import os
import platform
import select
import shlex
import subprocess as sp
import sys
import textwrap
import threading
import time
import tkinter as tk
import traceback
import uuid

from pydo import bases
from pydo.util import bash

MSEC = 1.0 / 1000.0

DEFAULT_SOCK = f'/dev/shm/{os.environ["USER"]}_ydo.sock'

def eprint(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    print(*args, **kwargs)

class Ignore(object):
    def write(self, data):
        return len(data)
    def flush(self):
        pass

class ToStderr(object):
    def __init__(self):
        self.decoder = codecs.getincrementaldecoder('utf-8')()
    def write(self, data):
        print(self.decoder.decode(data), end='', file=sys.stderr)
        return len(data)
    def flush(self):
        pass

def forward(src, dst):
    """Forward data from src to dst."""
    buf = bytearray(io.DEFAULT_BUFFER_SIZE)
    view = memoryview(buf)
    readinto = getattr(src, 'readinto1', src.readinto)
    amt = readinto(buf)
    while amt:
        total = 0
        while total < amt:
            total += dst.write(view[total:amt])
        amt = readinto(buf)
    dst.flush()

def readtil(f, target, bufsize=io.DEFAULT_BUFFER_SIZE, out=None):
    """Read file until target is found.

    f: the file to read from.
    target: The target bytes to search for.
    bufsize: The buffersize to use.
    out: output if buffer is filled but target not found.

    Return (index, buf, total)
        index: the index where target is found.
        buf: the buffer.
        total: the total number of bytes read.
    """
    buf = bytearray(max(bufsize, len(target)))
    view = memoryview(buf)
    total = 0
    readinto = getattr(f, 'readinto1', f.readinto)
    amt = readinto(view)
    minwin = len(target) - 1
    while amt:
        searchstart = max(0, total - minwin)
        total += amt
        idx = buf.find(target, searchstart, total)
        if idx >= 0:
            return idx, buf, total
        elif total == len(buf):
            if out is not None:
                out.write(view[:-minwin])
            view[:minwin] = view[-minwin:]
            total = minwin
        amt = readinto(view[total:])
    return -1, buf, total


class LinKeyboard(bases.Keyboard):
    # libinput names -> tk names
    # if decide want to parse the libinput output to auto-detect
    # which keys etc...
    libinputnames = {
        '0': '_0',
        '1': '_1',
        '2': '_2',
        '3': '_3',
        '4': '_4',
        '5': '_5',
        '6': '_6',
        '7': '_7',
        '8': '_8',
        '9': '_9',
        'A': 'a',
        'B': 'b',
        'C': 'c',
        'D': 'd',
        'E': 'e',
        'F': 'f',
        'G': 'g',
        'H': 'h',
        'I': 'i',
        'J': 'j',
        'K': 'k',
        'L': 'l',
        'M': 'm',
        'N': 'n',
        'O': 'o',
        'P': 'p',
        'Q': 'q',
        'R': 'r',
        'S': 's',
        'T': 't',
        'U': 'u',
        'V': 'v',
        'W': 'w',
        'X': 'x',
        'Y': 'y',
        'Z': 'z',
        'SPACE': 'space',
        'GRAVE': 'grave',
        'MINUS': 'minus',
        'EQUAL': 'equal',
        'LEFTBRACE': 'bracketleft',
        'RIGHTBRACE': 'bracketright',
        'BACKSLASH': 'backslash',
        'SEMICOLON': 'semicolon',
        'APOSTROPHE': 'apostrophe',
        'COMMA': 'comma',
        'DOT': 'period',
        'SLASH': 'slash',
        'ESC': 'Escape',
        'BACKSPACE': 'BackSpace',
        'ENTER': 'Return',
        'INSERT': 'Insert',
        'HOME': 'Home',
        'PAGEUP': 'Prior',
        'DELETE': 'Delete',
        'END': 'End',
        'PAGEDOWN': 'Next',
        'TAB': 'Tab',
        'CAPSLOCK': 'Caps_Lock',
        'SCROLLLOCK': 'Scroll_Lock',
        'NUMLOCK': 'Num_Lock',
        'PAUSE': 'Pause',
        'LEFTMETA': 'Super_L',
        'RIGHTMETA': 'Super_R',
        'LEFTALT': 'Alt_L',
        'RIGHTALT': 'Alt_R',
        'LEFTSHIFT': 'Shift_L',
        'RIGHTSHIFT': 'Shift_R',
        'LEFTCTRL': 'Control_L',
        'RIGHTCTRL': 'Control_R',
        'UP': 'Up',
        'LEFT': 'Left',
        'DOWN': 'Down',
        'RIGHT': 'Right',
        'KP0': 'kp_0',
        'KP1': 'kp_1',
        'KP2': 'kp_2',
        'KP3': 'kp_3',
        'KP4': 'kp_4',
        'KP5': 'kp_5',
        'KP6': 'kp_6',
        'KP7': 'kp_7',
        'KP8': 'kp_8',
        'KP9': 'kp_9',
        'KPASTERISK': 'kp_asterisk',
        'KPPLUS': 'kp_plus',
        'KPMINUS': 'kp_minus',
        'KPDOT': 'kp_dot',
        'KPSLASH': 'kp_slash',
    }

    _rawkeys = {
        '_0': 11,
        '_1': 2,
        '_2': 3,
        '_3': 4,
        '_4': 5,
        '_5': 6,
        '_6': 7,
        '_7': 8,
        '_8': 9,
        '_9': 10,
        'a': 30,
        'b': 48,
        'c': 46,
        'd': 32,
        'e': 18,
        'f': 33,
        'g': 34,
        'h': 35,
        'i': 23,
        'j': 36,
        'k': 37,
        'l': 38,
        'm': 50,
        'n': 49,
        'o': 24,
        'p': 25,
        'q': 16,
        'r': 19,
        's': 31,
        't': 20,
        'u': 22,
        'v': 47,
        'w': 17,
        'x': 45,
        'y': 21,
        'z': 44,
        'SPACE': 57,
        'GRAVE': 41,
        'MINUS': 12,
        'EQUAL': 13,
        'LEFTBRACE': 26,
        'RIGHTBRACE': 27,
        'BACKSLASH': 43,
        'SEMICOLON': 39,
        'APOSTROPHE': 40,
        'COMMA': 51,
        'DOT': 52,
        'SLASH': 53,
        'F1': 59,
        'F2': 60,
        'F3': 61,
        'F4': 62,
        'F5': 63,
        'F6': 64,
        'F7': 65,
        'F8': 66,
        'F9': 67,
        'F10': 68,
        'F11': 87,
        'F12': 88,
        'F13': 183,
        'F14': 184,
        'F15': 185,
        'F16': 186,
        'F17': 187,
        'F18': 188,
        'F19': 189,
        'F20': 190,
        'F21': 191,
        'F22': 192,
        'F23': 193,
        'F24': 194,
        'ESC': 1,
        'BACKSPACE': 14,
        'ENTER': 28,
        'INSERT': 110,
        'HOME': 102,
        'PAGEUP': 104,
        'DELETE': 111,
        'END': 107,
        'PAGEDOWN': 109,
        'TAB': 15,
        'CAPSLOCK': 58,
        'SCROLLLOCK': 70,
        'NUMLOCK': 69,
        'PAUSE': 119,
        'LEFTMETA': 125,
        'RIGHTMETA': 126,
        'LEFTALT': 56,
        'RIGHTALT': 100,
        'LEFTSHIFT': 42,
        'RIGHTSHIFT': 54,
        'LEFTCTRL': 29,
        'RIGHTCTRL': 97,
        'UP': 103,
        'LEFT': 105,
        'DOWN': 108,
        'RIGHT': 106,
        'KP0': 82,
        'KP1': 79,
        'KP2': 80,
        'KP3': 81,
        'KP4': 75,
        'KP5': 76,
        'KP6': 77,
        'KP7': 71,
        'KP8': 72,
        'KP9': 73,
        'KPASTERISK': 55,
        'KPPLUS': 78,
        'KPMINUS': 74,
        'KPDOT': 83,
        'KPSLASH': 98,

        # 'ZENKAKUHANKAKU': 85,
        # '102ND': 86,
        # 'RO': 89,
        # 'KATAKANA': 90,
        # 'HIRAGANA': 91,
        # 'HENKAN': 92,
        # 'KATAKANAHIRAGANA': 93,
        # 'MUHENKAN': 94,
        # 'KPJPCOMMA': 95,
        # 'KPENTER': 96,
        # 'SYSRQ': 99,
        # 'MUTE': 113,
        # 'VOLUMEDOWN': 114,
        # 'VOLUMEUP': 115,
        # 'POWER': 116,
        # 'KPEQUAL': 117,
        # 'KPCOMMA': 121,
        # 'HANGEUL': 122,
        # 'HANJA': 123,
        # 'YEN': 124,
        # 'COMPOSE': 127,
        # 'STOP': 128,
        # 'AGAIN': 129,
        # 'PROPS': 130,
        # 'UNDO': 131,
        # 'FRONT': 132,
        # 'COPY': 133,
        # 'OPEN': 134,
        # 'PASTE': 135,
        # 'FIND': 136,
        # 'CUT': 137,
        # 'HELP': 138,
        # 'CALC': 140,
        # 'SLEEP': 142,
        # 'WWW': 150,
        # 'COFFEE': 152,
        # 'BACK': 158,
        # 'FORWARD': 159,
        # 'EJECTCD': 161,
        # 'NEXTSONG': 163,
        # 'PLAYPAUSE': 164,
        # 'PREVIOUSSONG': 165,
        # 'STOPCD': 166,
        # 'REFRESH': 173,
        # 'EDIT': 176,
        # 'SCROLLUP': 177,
        # 'SCROLLDOWN': 178,
        # 'KPLEFTPAREN': 179,
        # 'KPRIGHTPAREN': 180,
        # 'UNKNOWN': 240,
    }

    def __init__(self):
        try:
            self._rawkeys = self.load_keyboard()
        except Exception:
            pass
        super(LinKeyboard, self).__init__()


    @staticmethod
    def load_keyboard():
        raise NotImplementedError
        # was it stdout or stderr, or did it specify an output file
        # I do not remember...
        p = sp.Popen(['sudo', 'libinput', 'record'], stdout=sp.PIPE)
        stdo, stde = p.communicate()
        #TODO parse stdo for actual dict
        return {
            LinKeyboard.libinputnames.get(k, k): v
            for k, v in libinput_keys.items()}

    def get(self, *args):
        self._rawkeys.get(*args)
    def update(self, *args):
        self._rawkeys.update(*args)
    def items(self):
        return self._rawkeys.items()
    def __contains__(self, key):
        return key in self._rawkeys
    def __getitem__(self, key):
        return self._rawkeys[key]


class ydotoold(object):
    """Context manager for the ydotoold daemon."""

    SCRIPT = textwrap.dedent('''
        trap '' SIGINT
        stdbuf -oL ydotoold -p {0} &
        pid=$!
        trap "kill $pid; rm "{1} EXIT
        wait $pid
        rm {0} && trap '' EXIT
        ''')

    def __init__(self, sock=None, verbose=False):
        """Initialize ydotoold.

        sock: The socket path for ydotoold.
        """
        if sock is None:
            sock = DEFAULT_SOCK
        self.verbose = verbose
        self.path = sock
        self.proc = None
        self.thread = None
        self.open()

    def __str__(self):
        """Return the ydotoold socket path."""
        return self.path

    def open(self):
        """Open ydotoold process if needed."""
        if self.proc is not None:
            return
        command = ['bash', '-c']
        if os.environ['USER'] != 'root':
            command.insert(0, 'sudo')
        qpath = shlex.quote(self.path)
        command.append(self.SCRIPT.format(qpath, shlex.quote(qpath)))
        proc = sp.Popen(command, stdout=sp.PIPE, bufsize=0)
        if self.verbose:
            out = ToStderr()
        else:
            out = Ignore()
        idx, buf, total = readtil(proc.stdout, b'READY', out=out)
        if idx < 0:
            raise RuntimeError('ydotoold exited without READY.')
        out.write(memoryview(buf)[:total])
        self.thread = threading.Thread(target=forward, args=[proc.stdout, out])
        self.thread.start()
        self.proc = proc
        return

    def close(self):
        if self.proc is not None:
            try:
                self.proc.terminate()
                self.thread.join()
            except Exception:
                eprint('ydotoold bash proc was ', self.proc.pid)
                traceback.print_exc()
            self.proc = None

    def __enter__(self):
        self.open()
        return self
    def __exit__(self, tp, exc, tb):
        self.close()
    def __del__(self):
        self.close()

class NoMouseAccel(object):
    """Context manager to disable mouse acceleration."""

    # TODO: how to turn off for other desktop environments?
    # TODO: How to detect which desktop environment?
    GET = ['gsettings', 'get', 'org.gnome.desktop.peripherals.mouse', 'accel-profile']
    SET = ['gsettings', 'set', 'org.gnome.desktop.peripherals.mouse', 'accel-profile']
    FLAT = "'flat'"
    def __init__(self):
        self.accel = []

    def push(self):
        self.accel.append(sp.check_output(self.GET).decode('utf-8'))
        if self.accel[-1] != self.FLAT:
            sp.check_output(self.SET + [self.FLAT])
        return self
    def pop(self):
        try:
            orig = self.accel.pop()
            if orig != self.FLAT:
                sp.check_output(self.SET + [orig])
        except IndexError:
            pass
        return self
    def close(self):
        while self.accel:
            self.pop()
    def __enter__(self):
        self.push()
        return self
    def __exit__(self, tp, exc, tb):
        self.pop()
    def __del__(self):
        self.close()

class ydo(bases.ydo):
    m = bases.Mouse
    k = LinKeyboard()

    def __init__(self, sockpath=None, daemon=False, noaccel=False, verbose=False, **kwargs):
        """Initialize ydo process."""
        if sockpath is None:
            sockpath = DEFAULT_SOCK
        self.sockpath = sockpath
        self.verbose = verbose
        self.bash = None
        self.pos = None
        self.noaccel = None
        self.daemon = None
        self.open(daemon, noaccel, **kwargs)

    def open(self, daemon, noaccel, **kwargs):
        if self.bash is not None:
            return
        partials = []
        try:
            partials.append(bash.Bash(stdout=sp.PIPE, **kwargs))
            if daemon:
                partials.append(ydotoold(sock=self.sockpath, verbose=self.verbose))
            else:
                partials.append(None)
            if noaccel:
                partials.append(NoMouseAccel())
                partials[-1].push()
            else:
                partials.append(None)
            partials.append(kwargs.get('pos', DragPos))
            partials[0]('export YDOTOOL_SOCKET={}'.format(shlex.quote(self.sockpath)))
            self.bash, self.daemon, self.noaccel, self.pos = partials
            del partials[:]
        finally:
            for partial in partials:
                partial.close()

    def close(self):
        if self.bash is None:
            return
        if self.noaccel is not None:
            self.noaccel.close()
            self.noaccel = None
        if self.daemon is not None:
            self.daemon.close()
            self.daemon = None
        self.pos.close()
        self.bash.close()
        self.bash = self.pos = None

    def lockstate(self, key='Caps_Lock'):
        # probably delegate to positioning methods.
        pass

    def screenshape(self):
        # probably delegate to positioning methods.
        pass

    def pos(self):
        pass

    def click(self, code, repeat=1, delay=25, **kwargs):
        """Click the mouse."""
        raise NotImplementedError

    def move(self, dx, dy, absolute=True):
        """Move the mouse (inexact)."""
        raise NotImplementedError

    def keypress(self, key, down=True, up=True, delay=0):
        """Press/release a key."""
        raise NotImplementedError

def detect_deiconify_motion_type(r, nsamples=0, verbose=False):
    """Detect whether a <Motion> will be visible or not after deiconify.

    On wayland, without a geometry change, there is often only 1
    <Configure> which overlaps with <Windows>.  As a result, the
    geometry change to tiny window before full screen is necessary to
    distinguish.

    From observation:
        system  <Motion>    <Configures>    <Configures> on <Enter>
        Windows no          1               1
        wsl     yes         6               5 (sometimes 6)
        X (vnc) no          4               4
        wayland yes*        2(sometimes 3)  2 (sometimes 3)
    *sometimes no... not consistent, not sure how to make it consistent.
    Return tuple: (
        Motion is expected?,
        number of configs before ready,
        number of configs before <Enter>)

    If nsamples, then each item is a list instead.

    A window is considered "ready" when the mouse position reads the
    correct <x,y> coordinates and a mouse click would be registered
    as an event.
    """
    if not nsamples:
        t = tk.Toplevel(r)
        # There generally seems to be a potential for double <Motion>
        # if mouse happens to be inside of t when it first deiconifies.
        # so make it tiny and out of the way corner/edge is much more likely
        # than some other position prbly...
        # It seems geometry +0+0 vs +5+5 results in an extra <Configure>
        # for X (so (vnc: 3->4) (wsl: 5->6) (arch wayland: (1-2) -> (2-3))
        t.overrideredirect()
        t.geometry('1x1+5+5')
        t.withdraw()
        total = 'pydo_total_configs'
        mid = 'pydo_preenter_configs'
        r.call('set', total, 0)
        r.call('set', mid, 0)
        if verbose:
            extraenter = f'puts "enterred... %x %y %X %Y [expr ${total}]"\n'
            extraconfig = f'\nputs "configure [expr ${total}]"'
            extramotion = f'puts "motioned %x %y %X %Y [expr ${total}]"\n'
            extracleanup = f'puts "Failed to auto-close"\n'
        else:
            extraenter = extraconfig = extramotion = ''
        t.bind('<Enter>', f'{extraenter}set {mid} [expr ${total}]\nif {{${total} == 4 || ${total} == 1}} {{destroy {t}}}')
        t.bind('<Configure>', f'set {total} [expr ${total} + 1]{extraconfig}')
        t.bind('<Motion>', f'{extramotion}destroy {t}')

        t.attributes('-topmost', True, '-fullscreen', True)
        ret = r.call('after', '500', f'{extracleanup}set {total} [expr -${total}]\ndestroy {t}')
        t.deiconify()
        t.wait_window()
        r.call('after', 'cancel', ret)
        config_count = r.exprlong(f'${total}')
        return (config_count != 1 and config_count != 4 and config_count > 0), config_count, r.exprlong(f'${mid}')
    else:
        ret = ([], [], [])
        for i in range(nsamples):
            for lst, val in zip(ret, detect_deiconify_motion_type(r, 0, verbose)):
                lst.append(val)
        return ret

class DragPos(object):
    """Mouse positioning.

    Hold a seldom-used mouse button in tk window and use callbacks
    to track mouse.
    """
    def __init__(self, ydo, unused=2):
        self.pos = None
        self.ydo = ydo
        self.tk = tk.Tk()
        self.tk.withdraw()
        self.tk.title('Drag Positioning')
        self.mb = getattr(
            self.ydo.m,
            ('LEFT', 'MIDDLE', 'RIGHT')[unused])
        self.tk.createcommand('MonitorPos', self._start)
        if detect_deiconify_motion_type(self.tk)[0]:
            self.tk.bind('<<Motion>', 'MonitorPos')
        else:
            self.tk.bind('<Enter>', 'MonitorPos')
        self.tk.createcommand('HideWindow', self._hide)
        self.tk.bind(f'<Button-{unused}>', 'HideWindow')
        self.tk.createcommand('StopPosition', self._stop)
        self.tk.bind(f'<ButtonRelease-{unused}>', 'StopPosition')
        self.tk.createcommand('UpdatePosition', self._update_position)
        self.tk.bind(f'<B{unused}-Motion>', 'UpdatePosition %X %Y')
        self.tk.createcommand('PauseMonitoring', self.pause)
        self.tk.bind('<Control-Escape>', 'PauseMonitoring.')

    def pause(self):
        self.ydo.click(self.mb | self.ydo.m.UP)
        self.tk.deiconify()
        self.tk.geometry('200x200+0+0')

    def resume(self):
        self.tk.deiconify()
        self.tk('-fullscreen', True, '-topmost', True)

    def _start(self):
        self.ydo.click(self.mb | self.ydo.m.DOWN)
    def _hide(self):
        self.tk.attributes('-fullscreen', False)
        self.tk.geometry('1x1+0+0')
    def _stop(self):
        self.tk.withdraw()

    def _update_position(self, x, y):
        self.pos = (int(x), int(y))

    def move(self, x, y, absolute=True):
        """Checked motion."""
        pass

class PopPos(object):
    """Mouse positioning.

    Use deiconify fullscreen topmost tk window to determine
    the mouse position.
    """
    pass




class DragMotion(object):
    """Use tkinter to read current mouse position using drag+motion."""
    INIT_TARGET = 'InitToTarget'
    MOVE_TARGET = 'MoveToTarget'
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.tk, self.done, self.W, self.H = self.open()

    def open(self):
        r = tk.Tk()
        r.geometry('1x1+0+0')
        r.withdraw()
        withmotion, _ = detect_deiconify_motion_type(r)
        r.createcommand(self.INIT_TARGET, self._initial_move)
        r.createcommand(self.MOVE_TARGET, self._move_to_target)
        r.bind('<ButtonRelease-1>', f'wm withdraw {r}')
        # TODO? move window depending on target and current mouse position
        r.bind('<Button-1>', f'wm attributes {r} -fullscreen false\nwm geometry {r} 1x1+0+0')
        # <Enter> fires too soon on arch x-wayland, how to handle?
        if withmotion:
            r.bind('<Motion>', f'{self.INIT_TARGET} %X %Y')
        else:
            r.bind('<Enter>', f'{self.INIT_TARGET} %X %Y')
        r.bind('<B1-Motion>', f'{self.MOVE_TARGET} %X %Y')
        return r, tk.IntVar(r, 0), r.winfo_screenwidth(), r.winfo_screenheight()

    def close(self):
        if getattr(self, 'tk', None) is not None:
            self.tk.destroy()
            self.tk = None

    def __enter__(self):
        if getattr(self, 'tk', None) is None:
            self.tk, self.down, self.W, self.H = self.open()
        return self
    def __exit__(self, tp, exc, tb):
        self.close()
    def __del__(self):
        self.close()

    def _move_to_target(self, *args):
        x, y = map(int, args)
        if self.verbose:
            eprint(x, y)
        dx = self.path[0] - x
        dy = self.path[1] - y
        if dx or dy:
            stepx = dx / max(1, abs(dx))
            stepy = dy / max(1, abs(dy))
            self.ydotool.bash(
                f'ydotool mousemove -x {stepx} -y {stepy}')
        else:
            self.path.popleft()
            self.path.popleft()
            if self.path:
                if self.verbose:
                    eprint('intermediate reached.')
                self._move_to_target(x, y)
            else:
                if self.verbose:
                    eprint('final target reached')
                self.ydotool.click('UP')
                self.done.set(1)

    def _initial_move(self, *args):
        print('enterred, going to click... to begin motion...')
        self.tk.update()
        self.ydotool.click('DOWN')
        self._move_to_target(*args)

    def move(self, ydotool, *coords):
        """Move mouse according to coords.

        coords: sequence of alternating x, y coordinates.
        """
        self.path = deque(coords)
        self.ydotool = ydotool
        try:
            self.tk.deiconify()
            self.tk.attributes('-fullscreen', True, '-topmost', False)
            self.tk.wait_variable(self.done)
        finally:
            self.path
            del self.ydotool



class MousePosition(object):
    """Use tkinter window to track mouse position."""

    HIDE_CMD = 'hide_mouse_position_reader'
    HOLD_CMD = 'hold_mouse_position_reader'
    RELEASE_CMD = 'release_mouse_position_reader'
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.lock = threading.Lock()
        self.updated = 0
        self.held = 0
        self.tk, self.step, self.W, self.H = self.open()

    def open(self):
        """Initialize a tk instance.

        Return the root and the screen shape.
        """
        r = tk.Tk()
        r.geometry(f'{r.winfo_screenwidth()}x{r.winfo_screenheight()}+0+0')
        r.attributes('-topmost', True, '-fullscreen', True)
        r.withdraw()
        r.createcommand(self.HIDE_CMD, self.hide)
        r.createcommand(self.HOLD_CMD, self.holdmouse)
        r.createcommand(self.RELEASE_CMD, self.releasemouse)
        r.bind('<Motion>', self.HIDE_CMD)
        r.bind('<Button-1>', self.HOLD_CMD)
        r.bind('<ButtonRelease-1>', self.RELEASE_CMD)
        return r, tk.IntVar(r, 0), r.winfo_screenwidth(), r.winfo_screenheight()

    def holdmouse(self):
        """Track current mouse state."""
        with self.lock:
            self.held = 1
        if self.verbose:
            eprint('hold')
    def releasemouse(self):
        """Track current mouse state."""
        with self.lock:
            self.held = 0
        if self.verbose:
            eprint('release')

    def close(self):
        if getattr(self, 'tk', None) is not None:
            self.tk.destroy()
            self.tk = None

    def __enter__(self):
        if self.tk is None:
            self.tk, self.step, self.W, self.H = self.open()
        return self
    def __exit__(self, tp, exc, tb):
        self.close()
    def __del__(self):
        self.close()

    def hide(self):
        with self.lock:
            self.updated = True
        if self.verbose:
            eprint('updated mouse position.')
        self.step.set(1)
        # Seems like tk.attributes turn on/off fullscreen
        # is necessary or sometimes mouse event does not fire
        # after deiconify.
        self.tk.attributes('-fullscreen', False)
        self.tk.withdraw()

    def pos(self):
        """Get currently stored mouse position."""
        with self.lock:
            self.updated = False
            return self.tk.winfo_pointerxy()

    def readmouse(self, force=True):
        """Read the current mouse position (if not already updated).

        This temporarily sets the tk window to fullscren to ensure that
        the mouse is within the window allowing reading its position.

        force: force updating mouse position (ignored if mouse is currently held.)
        """
        with self.lock:
            if self.held or (not force and self.updated):
                self.updated = False
                return self.tk.winfo_pointerxy()
        self.tk.deiconify()
        self.tk.attributes('-topmost', True, '-fullscreen', True)
        self.tk.wait_variable(self.step)
        return self.pos()

    def __del__(self):
        self.close()


class ydotool(object):
    """Ydotool commands through a bash process."""
    def __init__(self, sockpath=None, stderr=sp.DEVNULL, noaccel=False, verbose=False):
        self.verbose = verbose
        self.bash = None
        self.pos = None
        if noaccel:
            self.noaccel = NoMouseAccel()
        else:
            self.noaccel = None
        if sockpath is None:
            sockpath = DEFAULT_SOCK
        self.sockpath = sockpath
        self.open(stderr)

    def open(self, stderr=None):
        if self.bash is not None:
            return
        self.bash = bash.Bash(os.environ['USER'] != 'root', stdout=sp.PIPE, stderr=stderr)
        if self.noaccel is not None:
            self.noaccel.push()
        self.pos = MousePosition()
        self.bash(
            'export YDOTOOL_SOCKET={}'.format(
                shlex.quote(self.sockpath)))
        if self.bash(textwrap.dedent('''
            smove()
            {
                local x="${1}" y="${2}"
                if ((x == 0 && y == 0)); then return; fi
                if ((${x#*-} > ${y#*-}))
                then
                    local main=x sub=y
                else
                    local main=y sub=x
                fi
                local i=0 dx dy end=${!main#*-} step='++i'
                ((d${main} = ${!main//[^-]}1))
                if ((${!sub}))
                then
                    ((end *= ${!sub#*-}))
                    step=''
                    eval d${sub}='"${!sub//[^-]}(-(i / ${!main#*-}) + (i+=${!sub#*-})/${!main#*-})"'
                else
                    ((d${sub} = 0))
                fi
                for ((; i<end; step))
                do
                    ydotool mousemove -x $((dx)) -y $((dy))
                done
            }
            multimove() {
                while ((${#}))
                do
                    ydotool mousemove -x ${1} -y ${2}
                    shift 2
                done >&2
            }
            echo ready
            ''')).stdout.readline().strip() != b'ready':
            self.close()
            raise RuntimeError('Failed to start ydotool.')

    def sync(self):
        """Synchronize bash commands (echo and wait for output).

        This means that for most commands, stdout should be redirected away
        so synchronization does not possibly read some other command's output.
        """
        self.bash('echo').stdout.readline()

    def close(self):
        if self.bash is None:
            return
        if self.noaccel is not None:
            self.noaccel.close()
        self.pos.close()
        self.bash.close()
        self.bash = None


    def type(self, text, nextdelay=0, keydelay=12, flush=True):
        self.bash('ydotool type', shlex.quote(text), '>&2', flush=flush)

    LEFT = 0x00
    RIGHT = 0x01
    MIDDLE = 0x02
    SIDE = 0x03
    EXTR = 0x04
    FORWARD = 0x05
    BACK = 0x06
    TASK = 0x07

    DOWN = 0x40
    UP = 0x80
    def click(self, code=UP|DOWN|LEFT, repeat=1, delay=25, flush=True):
        if isinstance(code, str):
            newcode = 0
            for c in code.split('|'):
                newcode |= getattr(self, c)
            code = newcode
        self.bash(
            'ydotool click 0x{:02x}'.format(code),
            '--repeat', repeat,
            '--next-delay', delay,
            '>&2', flush=flush)

    # TODO maybe read/parse the mapping? ...
    # sudo libinput read -o out.yaml, sleep(1), terminate(),
    # then parse for key: name, form a dict, ...
    # is outputting to stdout possible? otherwise use process substitution?
    def keys(*specs):
        """Press keys in order.

        specs: str: the key to press (down then up)
               tuple: (key, state) where state = 1 (down), or 0 (up).
        """
        seq = []
        for spec in specs:
            if isinstance(spec, str):
                seq.append(spec + ':1')
                seq.append(spec + ':0')
            else:
                seq.append(':'.join((spec[0], int(bool(spec[1])))))
        # TODO

    def travel(self, coordinates, absolute=True, sleep=(lambda e:None)):
        """Move mouse approximately along the given coordinates.

        Coordinates: sequence of (x, y, delay)
            x,y: mouse screen coordinates.
            delay: time delay (ms).
        Due to mouse acceleration, the mouse might overshoot etc.
        After every move, iterate through coordinates until the
        first point that increases distance from the new cursor
        position.
        """
        x, y = self.pos.readmouse()
        if not absolute:
            ncoordinates = []
            lx, ly = x, y
            for (dx, dy, delay) in coordinates:
                lx += dx
                ly += dy
                ncoordinates.append((lx, ly, delay))
        ptidx = 0
        nx, ny, _ = coordinates[ptidx]
        while ptidx < len(coordinates):
            dx = nx-x
            dy = ny-y
            self.bash('ydotool mousemove -x {} -y {} >&2'.format(dx, dy))
            self.bash.stdout.readline()
            nx, ny = self.pos.readmouse()
            ax = nx-x
            ay = ny-y
            x,y = nx,ny
            lastdst = abs(ax) + abs(ay)
            delay = 0
            for ptidx in range(ptidx+1, len(coordinates)):
                nx, ny, dly = coordinates[ptidx]
                delay += dly
                dst = abs(nx-x) + abs(ny-y)
                if dst < lastdst:
                    lastdst = dst
                else:
                    break
            sleep(delay)
        self.move(nx, ny, True)

    def calibrate_motion(self, motion, samples=3, margin=10):
        """Convert a screen motion arc into a mousemotion arc.

        motion: [(x, y, delay)...]
        samples: number of consecutive successes to determine motion.
        reset: float (sec), number of seconds required to reset mouse.
        """
        def adjust_bounds(lo, hi, result, target):
            """Adjust the bounds of best mouse delta."""
            result = abs(result)
            target = abs(target)
            if result == target:
                return lo, hi
            else:
                mid = lo + (hi-lo)//2
                if result > target:
                    if lo == mid:
                        return max(lo-1, 1), mid
                    else:
                        return lo, mid
                else:
                    if lo == mid:
                        return mid, hi+1
                    else:
                        return mid, hi
        def prep_range(dx, dy):
            """Prepare the potential range of mouse delta"""
            sx = -1 if dx < 0 else (1 if dx > 0 else 0)
            sy = -1 if dy < 0 else (1 if dy > 0 else 0)
            return sx, sy, (1 if dx else 0), abs(dx*2), (1 if dy else 0), abs(dy*2)

        def pick_best(tx, ty, attempts):
            """Choose the best delta among the given attempts.

            tx, ty: target ending postion
            attempts: {(dx,dy): [(rx,ry), ...]} dict of mouse delta to resulting position.
            """
            bestdelta = None
            bestpos = None
            bestdif = None
            for delta, results in attempts.items():
                avgx = 0
                avgy = 0
                for x, y in results:
                    avgx += x
                    avgy += y
                avgx /= len(results)
                avgy /= len(results)
                diff = abs(avgx - tx) + abs(avgy - ty)
                if bestdelta is None or diff < bestdif:
                    bestdelta = delta
                    bestpos = (int(round(avgx)), int(round(avgy)))
                    bestdif = diff
            return bestdelta, bestpos

        def add_delta(motion, targetidx, calibrated, position, samples=3, margin=float('inf')):
            """Add a single delta to calibrated motion.

            motion: sequence of tuple: [(x,y,delay)...], screen positions,
                    delay in msec.
            calibrated: sequence of tuple: [(dx, dy, delay)...] mouse deltas,
                        delay in msec.
            position: estimated ending position of input calibrated.

            Return the new position.
            """
            tx, ty, delay = motion[targetidx]
            prex, prey = position
            dx = tx - prex
            dy = ty - prey
            eprint(f'target step: ({px}, {py}) -> ({tx}, {ty})')
            if dx == 0 and dy == 0:
                return position
            sx, sy, lox, hix, loy, hiy = prep_range(dx, dy)
            attempts = defaultdict(list)
            while 1:
                gx = (lox + (hix-lox)//2)*sx
                gy = (loy + (hiy-loy)//2)*sy
                self.move(motion[0][0], motion[0][1], True, 5)
                for x, y, t in calibrated:
                    time.sleep(t/1000.0)
                    self.bash(f'ydotool mousemove -x {x} -y {y} >&2; echo').stdout.readline()
                time.sleep(delay/1000.0)
                self.bash(f'ydotool mousemove -x {gx} -y {gy} >&2; echo').stdout.readline()
                x, y = self.pos.readmouse()
                eprint(f'  mouse guess ({gx},{gy}) -> screen ({x}, {y}):')
                attempts[(gx, gy)].append((x,y))
                if len(attempts[(gx,gy)]) >= samples:
                    bestdelta, bestpos = pick_best(tx, ty, attempts)
                    if bestdelta == (gx, gy):
                        if abs(bestpos[0] - tx) < margin and abs(bestpos[1] - ty) < margin:
                            calibrated.append(bestdelta + (delay,))
                            eprint(f'  final delta: {bestdelta}')
                            eprint(f'  final point: ({x}, {y})')
                            return bestpos
                        else:
                            eprint('  Not within margin.')
                            return None
                    eprint(f'    x: ({lox}-{hix}) -> ', end='')
                    lox, hix = adjust_bounds(lox, hix, x-prex, dx)
                    eprint(f'({lox}-{hix}), y: ({loy}-{hiy}) -> ', end='')
                    loy, hiy = adjust_bounds(loy, hiy, y-prey, dy)
                    eprint(f'({loy}-{hiy})')
        def best_idx(motion, position, idx):
            """Choose the best index for the next target given motion and current position and idx."""
            best = idx
            delta = abs(motion[idx][0] - position[0]) + abs(motion[idx][1] - position[1])
            for candidate in range(idx+1, len(motion)):
                ndelta = (abs(motion[candidate][0] - position[0])
                          + abs(motion[candidate][1] - position[1]))
                if ndelta < delta:
                    best = candidate
                    delta = ndelta
                else:
                    break
            return best
        calibrated = []
        position = motion[0][:2]
        idx = 1
        while idx < len(motion):
            position = add_delta(motion, idx, calibrated, position, samples, margin)
            nidx = best_idx(motion, position, idx)
            if nidx != len(motion)-1 or idx == nidx:
                idx = nidx+1
            else:
                idx = nidx
        return calibrated

    def calibrate3(self, msecs=range(0,2000,100), samples=3):
        data = {}
        for msec in msecs:
            data[msec] = []
            eprint('{:4d}: '.format(msec), end='')
            for i in range(samples):
                start = self.pos.readmouse()
                time.sleep(msec/1000.0)
                self.bash('ydotool mousemove -x 10 -y 10 >&2; echo').stdout.readline()
                stop = self.pos.readmouse()
                time.sleep(msec/1000.0)
                self.bash('ydotool mousemove -x -10 -y -10 >&2; echo').stdout.readline()
                data[msec].append((stop[0]-start[0], stop[1]-start[1]))
                eprint('({:4d}, {:4d}), '.format(*data[msec][-1]), end='')
            eprint()
        return data

    def calibrate2(self, cases=itertools.chain.from_iterable(
            [[(v,0), (0,v), (v, v), (v, v//2), (v//2, v)] for v in range(10, 100, 10)]),
        samples=3, wait=0):
        """Calibrate actual motion to mouse motion (single ydo call).

        cases: cases of relative mouse motions.
        samples: number of samples to collect for each case.
        wait: wait time after readmouse (idle mouse duration.)
        return {wait_time: {avg_screen_motion: required_mouse_motion}}
        """
        if isinstance(wait, (float, int)):
            wait = [wait]
        if not wait:
            wait = [0]
        results = {}
        for tm in wait:
            wresults = results[tm] = {}
            eprint(f'wait {tm:.3f} seconds')
            for delta in cases:
                eprint('  ({:4d}, {:4d}): '.format(*delta), end='')
                tx = 0
                ty = 0
                self.bash(
                    'ydotool mousemove -x {-delta[0]} -y {-delta[1]} >&2; echo'
                    ).stdout.readline()
                for sample in range(samples):
                    p1 = self.pos.readmouse()
                    if tm:
                        time.sleep(tm)
                    self.bash('ydotool mousemove -x {} -y {} >&2; echo'.format(
                        *delta)).stdout.readline()
                    p2 = self.pos.readmouse()
                    if tm:
                        time.sleep(tm)
                    self.bash(
                        f'ydotool mousemove -x {-delta[0]} -y {-delta[1]} >&2; echo'
                        ).stdout.readline()
                    dx = p2[0]-p1[0]
                    dy = p2[1]-p1[1]
                    eprint(f'({dx:4d}, {dy:4d}), ', end='')
                    tx += dx
                    ty += dy
                eprint()
                tx /= samples
                ty /= samples
                wresults[(int(round(tx)), int(round(ty)))] = delta
        return results

    def calibrate(
        self,
        cases=itertools.chain.from_iterable(
            [[(v,0), (0,v), (v, v), (v, v//2), (v//2, v)] for v in range(10, 100, 10)]),
        samples=3, wait=0
    ):
        """Calibrate actual motion to mouse motion (incremental 1-pix loop).

        cases: list of (x,y) relative mouse motions.
        samples: int, number of samples to measure per case.
        wait: amount of time to wait just before moving the mouse.
              (idle mouse duration.)
        Return {wait_time: {avg_screen_motion: required_mouse_motion}}
        """
        def reset(dim):
            mid = (self.pos.W//2, self.pos.H//2)
            target = [0, 0]
            target[1-dim] = mid[1-dim]
            pos = self.pos.readmouse()
            while pos[dim] != 0:
                dx = (target[0] - pos[0])
                dy = (target[1] - pos[1])
                if abs(dx) > 1:
                    dx //= 2
                if abs(dy) > 1:
                    dy //= 2
                self.bash('smove', dx, dy, ' >&2; echo').stdout.readline()
                pos = self.pos.readmouse()
        if isinstance(wait, (float, int)):
            wait = [wait]
        if not wait:
            wait = [0]
        results = {}
        for tm in wait:
            wresults = results[tm] = {}
            eprint(f'wait {tm:.3f} seconds')
            for delta in cases:
                eprint('  ({:4d}, {:4d}): '.format(*delta), end='')
                tx = 0
                ty = 0
                for sample in range(samples):
                    reset(int(delta[1] > delta[0]))
                    p1 = self.pos.readmouse()
                    if tm:
                        time.sleep(tm)
                    self.bash(
                        'smove {} {} >&2\necho'.format(*delta)).stdout.readline()
                    p2 = self.pos.readmouse()
                    dx = p2[0]-p1[0]
                    dy = p2[1]-p1[1]
                    eprint(f'({dx:4d}, {dy:4d}), ', end='')
                    tx += dx
                    ty += dy
                eprint()
                tx /= samples
                ty /= samples
                wresults[(int(round(tx)), int(round(ty)))] = delta
        return results

    def cmove(self, x, y, calibration, absolute=False):
        """Calculate the mouse (mx,my) to move for screen motion (x,y).

        x, y: int, The desired screen movement.
        calibration: dict, result of calibrate(),
                     {waittime: {screenmotion: mousemotion}}.
        absolute: bool, Indicate whether x,y are absolute coordinates.
        """
        if absolute:
            x, y = [d-s for d, s in zip((x,y), self.pos.readmouse())]
        wt = min(calibration)
        curve = calibration[wt]
        target = (x, y)
        mousemotion = []
        for dim in range(2):
            val = abs(target[dim])
            if val == 0:
                mousemotion.append(0)
                continue
            lo = hi = None
            for screen in curve:
                check = abs(screen[dim])
                if check == val:
                    lo = hi = screen
                elif check < val:
                    if lo is None or abs(lo[dim]) < check:
                        lo = screen
                else:
                    if hi is None or check < abs(hi[dim]):
                        hi = screen
            if lo is None or hi is None or lo == hi:
                screen = lo or hi
                mouse = curve[screen]
                mousemotion.append(int(round(target[dim] * abs(mouse[dim]) / abs(screen[dim]))))
            else:
                lomouse = abs(curve[lo][dim])
                loscreen = abs(lo[dim])
                himouse = abs(curve[hi][dim])
                hiscreen = abs(hi[dim])
                mousemotion.append(
                    int(round(
                        lomouse
                        +(val-loscreen)*(himouse-lomouse)/(hiscreen-loscreen))))
                if target[dim] < 0:
                    mousemotion[-1] *= -1
        return mousemotion

    def move(self, x, y, absolute=False, check=5):
        """Move mouse to x, y.

        x, y: move the mouse by x,y.
        absolute: Move to (x,y) as measure from the top-left corner.
                  Note that ydotool does not have a "real" absolute
                  movement.  All it does is move a large offset to the
                  topleft to reset the mouse to (0,0) before moving
                  the given (x,y).  This can cause problems, such as if
                  gnome hot corner is turned on.
                  If given as ((rt)(lb)), then use that corner
                  as the target corner to move to for resetting the mouse
                  position.
        check: Check progress every 5 iterations. If the mouse position
               is not closer to the target, then stop.  This allows
               accurate movement even with mouse acceleration.
               For now, this is implemented by flashing a full screen
               topmost tkinter window (see `MousePosition`) so the window
               will flash on the screen with each measurement.
        """
        if check:
            cx, cy = self.pos.readmouse()
            if not absolute:
                x += cx
                y += cy
            x = min(max(x, 0), self.pos.W-1)
            y = min(max(y, 0), self.pos.H-1)
            dx = x-cx
            dy = y-cy
            odst = abs(dx) + abs(dy)
            it = 0
            while 1:
                self.bash('ydotool mousemove -x {} -y {} >&2'.format(dx, dy), flush=False)
                self.sync()
                nx, ny = self.pos.readmouse()
                if (nx, ny) == (x,y):
                    if self.verbose:
                        eprint('arrived to target.')
                    return
                if nx == cx:
                    if nx == x:
                        dx = 0
                    else:
                        dx = x - nx
                else:
                    dx = int(((x-nx)*dx) / (nx-cx))
                if ny == cy:
                    if ny == y:
                        dy = 0
                    else:
                        dy = y-ny
                else:
                    dy = int(((y-ny)*dy) / (ny-cy))
                if self.verbose:
                    eprint('  previous:', cx, cy, 'current:', nx, ny, 'target', x, y, 'adjusted:', dx, dy)
                cx = nx
                cy = ny
                it += 1
                if it >= check:
                    ndst = abs(x-cx) + abs(y-cy)
                    if ndst >= odst:
                        return
                    odst = ndst
                    it = 0
        else:
            if self.noaccel is None:
                eprint('WARNING: unchecked movement without noaccel.')
            if absolute:
                W, H = self.pos.W, self.pos.H
                W = (-W, W)['r' in absolute]
                H = (-H, H)['b' in absolute]
                self.bash((
                    'ydotool mousemove -x 0 -y {} >&2\n'
                    'ydotool mousemove -x {} -y 0 >&2\n'
                    'ydotool mousemove -x {} -y {} >&2'
                    ).format(H, W, x-max(0, W-1), y-max(0, H-1)))
            else:
                self.bash('ydotool mousemove -x {} -y {} >&2'.format(x, y))

    def __enter__(self):
        self.open()
        return self
    def __exit__(self, tp, exc, tb):
        self.close()
    def __del__(self):
        self.close()

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('-d', '--daemon', action='store_true')
    p.add_argument(
        '-c', '--calibrate', type=float, nargs='*',
        help='seconds to wait for calibration.')
    p.add_argument(
        '--calibrate2', type=float, nargs='*',
        help='seconds to wait for calibration.')
    p.add_argument('--mtype', action='store_true')
    p.add_argument('-y', '--ydotool', action='store_true')
    p.add_argument('--drag', action='store_true')
    args = p.parse_args()
    if args.daemon:
        with ydotoold() as d:
            try:
                input('Press return to exit.')
            except KeyboardInterrupt:
                pass
    elif args.ydotool:
        with ydotool() as y:
            import code
            code.interact(local=locals())
    elif args.mtype:
        r = tk.Tk()
        r.withdraw()
        verbose = True
        while 1:
            cmd = input('>>> ')
            if cmd == 'exit':
                break
            elif cmd.lower() == 'false' or cmd.lower() == 'true':
                verbose = cmd.lower() == 'true'
                print('verbose:', verbose)
                continue
            print(detect_deiconify_motion_type(r, (int(cmd) if cmd.isdigit() else 0), True))
    elif args.calibrate is not None:
        with ydotool() as y:
            y.calibrate(wait=args.calibrate)
    elif args.calibrate2 is not None:
        with ydotool() as y:
            y.calibrate2(wait=args.calibrate2)
    elif args.ydotool:
        with ydotool() as y:
            import code
            code.interact(local=locals())
    elif args.drag:
        import ast
        with ydotool() as y:
            with DragMotion(True) as drag:
                while 1:
                    target = input('>>> ')
                    if not target or target == 'exit':
                        break
                    target = ast.literal_eval(target)
                    drag.move(y, *target)
                    print('arrived')
    else:
        with MousePosition(True) as m:
            t = tk.Toplevel(m.tk)
            t.title('top')
            t.bindtags((str(m.tk),) + t.bindtags())
            t.bind('<space>', lambda e: print(m.readmouse(False)))
            t.bind('<Return>', lambda e: print(m.readmouse(True)))
            t.bind('<Escape>', 'destroy '+str(t))
            t.wait_window()
