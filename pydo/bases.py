import time
MSEC = 1.0 / 1000.0
class ydo(object):
    def lockstate(self, key):
        """State of caps, scroll, or numlock."""
        raise NotImplementedError

    def screenshape(self):
        """Return the screen dimensions (W,H)."""
        raise NotImplementedError

    def pos(self):
        """Return the mouse position (x,y)."""
        raise NotImplementedError

    def click(self, code, repeat=1, delay=25, **kwargs):
        """Click the mouse."""
        raise NotImplementedError

    def move(self, dx, dy, absolute=True):
        """Move the mouse (inexact)."""
        raise NotImplementedError

    def keypress(self, key, down=True, up=True, delay=0):
        """Press/release a key."""
        raise NotImplementedError

    def __enter__(self):
        return self
    def __exit__(self, tp, exc, tb):
        self.close()
    def close(self):
        pass

    def type(self, *texts, **kwargs):
        """Type the given text.

        texts: words to type (separated by a space).

        kwargs:
        nextdelay: int(msec)=0, delay between strings.
        keydelay: int(msec)=12, delay between key events.
        """
        nextdelay = kwargs.get('nextdelay', 0)
        keydelay = kwargs.get('keydelay', 12)
        keyboard = self.k
        shift = keyboard['Shift_L']
        caps = self.lockstate('Caps_Lock')

        for tidx, text in enumerate(texts):
            if tidx:
                if nextdelay:
                    time.sleep(nextdelay*MSEC)
                self.keypress(keyboard.space, delay=keydelay)
                time.sleep(keydelay*MSEC)
            if caps:
                text = text.swapcase()
            for i, k in enumerate(text):
                if i:
                    time.sleep(keydelay*MSEC)
                if k in keyboard:
                    self.keypress(keyboard[k], delay=keydelay)
                elif k in keyboard.shift:
                    self.keypress(shift, up=False)
                    self.keypress(keyboard.shift[k], delay=keydelay)
                    self.keypress(shift, down=False)


class Mouse(object):
    LEFT = 0x0
    RIGHT = 0x1
    MIDDLE = 0x2
    SIDE = 0x3
    EXTR = 0x4
    FORWARD = 0x5
    BACK = 0x6
    TASK = 0x7
    DOWN = 0x40
    UP = 0x80

class Keyboard(object):
    ALIASES = [
        '0_0',
        '1_1',
        '2_2',
        '3_3',
        '4_4',
        '5_5',
        '6_6',
        '7_7',
        '8_8',
        '9_9',
        '\tTab',
        '\nReturn',
        ' space',
        '`grave',
        '-minus',
        '=equal',
        '[bracketleft',
        ']bracketright',
        '\\backslash',
        ';semicolon',
        '\'apostrophe',
        ',comma',
        '.period',
        '/slash',
    ]
    NOSHIFT = 'abcdefghijklmnopqrstuvwxyz`1234567890-=[]\\;\',./'
    SHIFTED = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ~!@#$%^&*()_+{}|:"<>?'
    def __init__(self):
        self.update({alias[:1]: self[alias[1:]] for alias in self.ALIASES})
        self.shift = {newk: self[oldk] for newk, oldk in zip(self.SHIFTED, self.NOSHIFT)}

    def __getattr__(self, attr):
        try:
            ret = self[attr]
        except KeyError:
            raise AttributeError(attr)
        else:
            setattr(self, attr, ret)
            return ret

    def key(self, k):
        """Return (shift_needed, intkey) from strkey."""
        try:
            return False, self[k]
        except KeyError:
            return True, self.shift[k]

    def name(self, val):
        """Find the strkey given the intkey."""
        for k, v in self.items():
            if v == val:
                return k
        raise KeyError('No key matches value {}'.format(val))
