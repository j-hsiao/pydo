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
        '0zero',
        '1one',
        '2two',
        '3three',
        '4four',
        '5five',
        '6six',
        '7seven',
        '8eight',
        '9nine',
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
        raise KeyError(f'No key to match value {val}')
