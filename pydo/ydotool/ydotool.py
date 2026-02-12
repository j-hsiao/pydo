class Context(object):
    def __enter__(self):
        if not self:
            self.open()
        return self
    def __exit__(self, tp, exc, tb):
        self.close()
    def __bool__(self):
        return True
    def close(self):
        pass
    def open(self, *args, **kwargs):
        pass

class ydotoold(Context):
    def __init__(self, *args, **kwargs):
        pass

class ydotool(Context):
    """Basic ydotool functionality.

    Move/click the moouse (might or might not be affected by
    acceleration)
    Press keys.
    """

    def move(self, x, y, absolute=True):
        """Move the mouse.

        x, y: int, The mouse coordinates.
        absolute=True: bool, If absolute, then x,y are absolute screen
                       coordinates, otherwise, they are relative motions.
        """
        raise NotImplementedError

    def compile_clicks(self, codes):
        """Compile clicks for click().

        codes: a sequence of `pydo.ydotool.mouse.Mouse.*` int constants.
        """
        raise NotImplementedError

    def click(self, *codes, **kwargs):
        """Perform mouse click(s).

        codes: sequence of clicks taken by `compile_clicks()`
               or the result of `compile_clicks()`
               If omitted, default to a left click.
        kwargs:
            delay=25: int(msec), delay between mouse click events (down, up)
            repeat=1: int, number of times to perform the clicks.
        """
        raise NotImplementedError

    def compile_keys(self, keys):
        """Compile keypresses for keypress().

        keys: a sequence of keypresses in the form of key[:0|1].
              where key is the name of a key and [:0|1], if present,
              indicate release or press respectively.  If absent, then
              it indicates press followed by release.
        """
        raise NotImplementedError

    @staticmethod
    def normalize_keys(inst, keys):
        """Normalize keys into single-key events.

        Key only is translated to down followed by up.
        If shift is required, then it will be pressed
        and released.
        """
        SHIFT = inst.k['Shift_L']
        shifted = False
        for key in keys:
            parts = key.split(':', 1)
            key = parts[0]
            ev = parts[1:]
            if not ev:
                ev = ('1', '0')
            shift, knum = inst.k(key)
            if knum is None:
                raise ValueError('bad key: {}'.format(repr(key)))
            if shift != shifted:
                if shift:
                    yield SHIFT, '1'
                else:
                    yield SHIFT, '0'
                shifted = shift
            for v in ev:
                yield (knum, v)
        if shifted:
            yield SHIFT, '0'

    def keypress(self, *keys, **kwargs):
        """Perform keypress(es).

        keys: sequence of keys taken by `compile_keys()`.
              or the result of `compile_keys()`
        kwargs:
            delay=12: int(msec)
        """
        raise NotImplementedError

    def type(self, *words, **kwargs):
        """Type the given text.

        text: sequence of str words to type.

        kwargs:
            delay=0: int(msec), delay between words
            keydelay=12: int(msec), delay between key events
        """
        raise NotImplementedError


    def refresh(self):
        """Refresh any cached state."""
        pass
