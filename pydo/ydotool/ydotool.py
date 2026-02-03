class ydotool(object):
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
        kwargs:
            delay=25: int(msec), delay between mouse click events (down, up)
            repeat=0: int, number of repetitions.
        """
        # TODO repeat=1 is do it once, or do it twice (first + 1 repeat)?
        raise NotImplementedError

    def compile_keys(self, keys):
        """Compile keypresses for keypress().

        keys: a sequence of keypresses in the form of key[:0|1].
              where key is the name of a key and [:0|1], if present,
              indicate release or press respectively.  If absent, then
              it indicates press followed by release.
        """
        raise NotImplementedError

    def keypress(self, *keys, **kwargs):
        """Perform keypress(es).

        keys: sequence of keys taken by `compile_keys()`.
              or the result of `compile_keys()`
        kwargs:
            delay=12: int(msec)
        """
        raise NotImplementedError

    def type(self, *text, **kwargs):
        """Type the given text.

        text: sequence of words to type.

        kwargs:
            delay=0: int(msec), delay between words
            keydelay=12: int(msec), delay between key events
        """
        raise NotImplementedError
