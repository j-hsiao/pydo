import platform

if platform.system() == 'Windows':
    pass
else:
    pass
    class ydotool(object):
        """Basic ydotool functionality.

        Move/click the moouse (might or might not be affected by
        acceleration)
        Press keys.
        """

        def mousemove(self, x, y, absolute=True):
            """Move the mouse."""
            raise NotImplementedError

        def click(self, code):
            """Click the mouse."""
            raise NotImplementedError

        def keypress(self, key, down=True, up=True, delay=0):
            """Press/release a key."""
            raise NotImplementedError
