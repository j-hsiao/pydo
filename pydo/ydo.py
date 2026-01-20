class ydotool(object):
    def type(self, text, nextdelay=0, keydelay=12):
        """Type the given text.

        nextdelay: delay between actions (up/down)
        keydelay: delay between keys
        """
        keyboard = self.k
        shift = keyboard['Shift_L']
        if self.lockstate('Caps_Lock'):
            text = text.swapcase()
        for i, k in enumerate(text):
            if i:
                time.sleep(keydelay*MSEC)
            if k in keyboard:
                self.keypress(keyboard[k])
            elif k in keyboard.shift:
                self.keypress(shift, up=False)
                self.keypress(keyboard.shift[k], delay=nextdelay)
                self.keypress(shift, down=False)

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
