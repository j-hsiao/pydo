from .mouse import Mouse
from .keyboard import DictKeyboard
from pydo.util import bash

import io
import os
import shlex
import subprocess as sp
import tempfile
import textwrap
import threading
import time
import traceback

class LinKeyboard(DictKeyboard):
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

    keys = {
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
        'space': 57,
        'grave': 41,
        'minus': 12,
        'equal': 13,
        'bracketleft': 26,
        'bracketright': 27,
        'backslash': 43,
        'semicolon': 39,
        'apostrophe': 40,
        'comma': 51,
        'period': 52,
        'slash': 53,
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
        'Escape': 1,
        'BackSpace': 14,
        'Return': 28,
        'Insert': 110,
        'Home': 102,
        'Prior': 104,
        'Delete': 111,
        'End': 107,
        'Next': 109,
        'Tab': 15,
        'Caps_Lock': 58,
        'Scroll_Lock': 70,
        'Num_Lock': 69,
        'Pause': 119,
        'Super_L': 125,
        'Super_R': 126,
        'Alt_L': 56,
        'Alt_R': 100,
        'Shift_L': 42,
        'Shift_R': 54,
        'Control_L': 29,
        'Control_R': 97,
        'Up': 103,
        'Left': 105,
        'Down': 108,
        'Right': 106,
        'kp_0': 82,
        'kp_1': 79,
        'kp_2': 80,
        'kp_3': 81,
        'kp_4': 75,
        'kp_5': 76,
        'kp_6': 77,
        'kp_7': 71,
        'kp_8': 72,
        'kp_9': 73,
        'kp_asterisk': 55,
        'kp_plus': 78,
        'kp_minus': 74,
        'kp_dot': 83,
        'kp_slash': 98,

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
            self.keys = self.load_keyboard()
        except Exception:
            pass
        super(LinKeyboard, self).__init__()

    @staticmethod
    def get_devices():
        """Return devices as seen by libinput.

        Keyboards seem to have
        1. keyboardName
        2. keyboardName System Control (handles special buttons power, screen brightness, sleep, etc)
        3. keyboardName Consumer Control (handles special buttons (volume up/down, play/pause/next, etc))

        NOTE: not sure why, but keyboard sometimes seems to be duplicated...
              libinput on the 2nd duplicate said no events so deleted the file...

        Useful keys:
            Device          device name
            Id              usb:... or host:... (would it be host:... for a laptop? dunno...)
            Capabilities    keyboard | pointer | keyboard pointer
            Kernel          /dev/input/event* (arg to libinput record to record that device)

        example:
            Power Button
            Power Button
            Sleep Button
            USB Keyboard
            USB Keyboard Consumer Control
            USB Keyboard System Control
            USB Keyboard (only had brightness and micmute controls)
        """
        if os.environ.get('USER', None) != 'root':
            cmd = ['sudo', 'libinput', 'list-devices']
        else:
            cmd = ['libinput', 'list-devices']
        p = sp.Popen(cmd, stdout=sp.PIPE)
        devices = []
        for line in p.stdout:
            line = line.decode().strip()
            if line:
                key, val = line.split(':', 1)
                if key == 'Device':
                    devices.append({})
                devices[-1][key] = val.strip()
        return devices

    @staticmethod
    def get_keyboards():
        """Filter through devices to find keyboards.

        Return {devid: [dev1, dev2, ...]}
        """
        devices = LinKeyboard.get_devices()
        keyboards = {}
        for dev in devices:
            if (
                dev['Capabilities'] == 'keyboard'
                and not dev['Device'].endswith('System Control')
                and not dev['Device'].endswith('Consumer Control')
                and dev['Device'] not in ('Power Button', 'Sleep Button')):
                keyboards.setdefault(dev['Id'], []).append(dev)
        return keyboards

    @staticmethod
    def load_keyboard():
        keyboards = LinKeyboard.get_keyboards()
        cmd = []
        if os.environ.get('USER') != 'root':
            cmd = ['sudo']
        cmd += ['libinput', 'record']
        for keyboard, devs in keyboards.items():
            for dev in devs:
                cmd.append(dev['Kernel'])
                print(cmd)
                try:
                    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.DEVNULL)
                finally:
                    cmd.pop()
                try:
                    keycodes = {}
                    keyevent = False
                    for line in p.stdout:
                        line = line.strip().decode()
                        if line.startswith('events:'):
                            if 'A' in keycodes:
                                return {
                                    LinKeyboard.libinputnames.get(k, k): v
                                    for k, v in keycodes.items()}
                            break
                        elif line.startswith('#'):
                            if line.startswith('# Event type'):
                                keyevent = line.endswith('(EV_KEY)')
                            elif keyevent:
                                query = line[1:].lstrip()
                                if query.startswith('Event code'):
                                    _, _, num, desc = query.split(None, 4)
                                    keycodes[desc.split('_', 1)[-1][:-1]] = int(num)
                finally:
                    p.terminate()
                    p.communicate()
        raise ValueError('Keyboard Check Failed.')


class ydotoold(object):
    SCRIPT = textwrap.dedent('''
        trap '' SIGINT
        stdbuf -oL ydotoold -p {0} &
        pid=$!
        trap "kill $pid; rm "{1} EXIT
        ''')

    def __init__(self, *args, **kwargs):
        self.socket = None
        self.verbose = None
        self.thread = None
        self.proc = None
        self.open(*args, **kwargs)

    def open(self, socket=None, verbose=None):
        if socket is None:
            if self.socket is None:
                socket = os.path.join('/dev/shm', os.environ.get('USER', '').join(('pydo_', '.sock')))
            else:
                socket = self.socket
        if verbose is None:
            verbose = False if self.verbose is None else self.verbose
        proc = bash.Bash(
            sudo=(os.environ.get('USER', '') != 'root'),
            stdout=sp.PIPE, bufsize=0)
        try:
            proc('trap "" SIGINT')
            qsock = shlex.quote(socket)
            proc('stdbuf -oL ydotoold -p {} &'.format(qsock))
            proc('pid=$!')
            if verbose:
                out = getattr(sys.stderr, 'buffer', sys.stderr)
            else:
                out = None
            buf, amt = self.read_til(proc.stdout, target=b'READY', out=out)
            if verbose:
                out.write(memoryview(buf)[:amt])
            t = threading.Thread(target=self.forward, args=(proc.stdout, out))
            t.start()
            proc('trap "kill $pid; rm "{} EXIT'.format(shlex.quote(qsock)))
            self.close()
            self.thread = t
            self.socket = socket
            self.verbose = verbose
            self.proc = proc
        finally:
            if self.proc is not proc:
                proc.close()

    def close(self):
        if self.proc is None:
            return
        try:
            self.proc.close()
        except Exception:
            print('Failed to close ydotoold bash process:', self.proc.pid, file=sys.stderr)
            traceback.print_exc()
        else:
            self.thread.join()
        finally:
            self.proc = None
            self.thread = None

    def __str__(self):
        return self.socket

    @staticmethod
    def forward(f1, f2):
        write = type if f2 is None else f2.write
        for line in f1:
            write(line)

    @staticmethod
    def read_til(f, target=b'READY', bufsize=io.DEFAULT_BUFFER_SIZE, out=None):
        """Read until a target sequence.

        Return buffer and amount of data.
        """
        overlap = len(target)-1
        buf = bytearray(max(bufsize, len(target)))
        view = memoryview(buf)
        total = 0
        readinto = getattr(f, 'readinto1', f.readinto)
        amt = readinto(view)
        while amt:
            end = total + amt
            idx = buf.find(target, max(0, total-overlap), end)
            if idx >= 0:
                if out is not None:
                    out.write(view[:idx])
                total = end-idx
                view[:total] = view[idx:end]
                return buf, total
            elif end == len(buf):
                if out is not None:
                    out.write(view[:-overlap])
                view[:overlap] = view[:-overlap]
                end = overlap
            total = end
            amt = readinto(view[total:])
        return None, None



class ydotool(object):
    """Basic ydotool functionality.

    Move/click the moouse (might or might not be affected by
    acceleration)
    Press keys.
    """
    def __init__(self, *args, **kwargs):
        """Initialize ydotool.

        daemon: bool, Start a daemon too.
        """
        self.bash = None
        self.daemon = None
        self.open(*args, **kwargs)

    def close(self):
        if self.daemon is not None:
            try:
                self.daemon.close()
            except Exception:
                traceback.print_exc()
            finally:
                self.daemon = None
        if self.bash is not None:
            try:
                self.bash.close()
            except Exception:
                traceback.print_exc()
            finally:
                self.bash = None

    def open(self, daemon=False, socket=None, verbose=False, **kwargs):
        sudo = os.environ.get('USER', '') != 'root'
        if socket is None:
            socket = os.path.join('/dev/shm', os.environ.get('USER', '').join(('pydo_', '.sock')))
        if verbose:
            kwargs.setdefault('stderr', None)
        if daemon:
            daemonproc = ydotoold(socket)
        else:
            daemonproc = None
        try:
            bashproc = bash.Bash(sudo=sudo, stdout=bash.sp.PIPE, **kwargs)
            try:
                bashproc('export YDOTOOL_SOCKET={}'.format(shlex.quote(socket)))
                self.close()
                self.bash = bashproc
                self.daemon = daemonproc
            finally:
                if self.bash is not bashproc:
                    bashproc.close()
        finally:
            if daemon and self.daemon is not daemonproc:
                daemonproc.close()

    def mousemove(self, x, y, absolute=True):
        """Move the mouse."""
        self.bash('ydotool mousemove -x {} -y {} >&2\necho'.format(x, y)).stdout.readline()

    def click(self, code):
        """Click the mouse."""
        self.bash('ydotool click 0x{:02x} >&2\necho'.format(code)).stdout.readline()

    def keypress(self, key, down=True, up=True, delay=0):
        """Press/release a key."""
        raise NotImplementedError


    def type(self, text, nextdelay=0, keydelay=12, flush=12):
        """Type text.

        nextdelay: int(msec), delay between words.
        keydelay: int(msec), delay between keystrokes.
        """
        self.bash(
            'ydotool type', shlex.quote(text),
            # TODO verify these arguments
            # '--next-delay', nextdelay,
            # '--key-delay', keydelay,
            '>&2\necho'
        ).stdout.readline()
