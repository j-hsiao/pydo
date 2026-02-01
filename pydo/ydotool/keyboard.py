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

class DictKeyboard(Keyboard):
    """Keyboard with keys stored in "keys" dict."""
    def get(self, *args, **kwargs):
        self.keys.get(*args, **kwargs)
    def update(self, *args, **kwargs):
        if self.keys is type(self).keys:
            self.keys = self.keys.copy()
        self.keys.update(*args, **kwargs)
    def items(self):
        return self.keys.items()
    def __contains__(self, key):
        return key in self.keys
    def __getitem__(self, key):
        return self.keys[key]

