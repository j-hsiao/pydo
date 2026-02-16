class Active(object):
    def __enter__(self):
        return self
    def __exit__(self, tp, exc, tb):
        pass

class ydo(object):
    def lockstate(self, key='Caps_Lock'):
        """Return state of the given lock.

        Caps_Lock, Num_Lock, Scroll_Lock
        """
        raise NotImplementedError

    def activate(self):
        """Return a context manager to activate this tool."""
        return Active()

    def screensize(self):
        """Return (W,H), size of screen."""
        raise NotImplementedError

    def pos(self):
        """Return (X,Y), current cursor position."""
        raise NotImplementedError

    def move(self, x, y, absolute=True):
        """Move cursor, ensuring accuracy."""
        if not absolute:
            cx, cy = self.pos()
            x += cx
            y += cy
        sW, sH = self.screensize()
        tpos = (max(0, min(sW, x)),max(0, min(sH, y)))
        super(ydo, self).move(x, y, True)
        npos = self.pos()
        scale = 1.0
        delta = [0, 0]
        while npos != tpos:
            for i in (0,1):
                d = tpos[i] - npos[i]
                if d < 0:
                    d = min(int(d*scale), -1)
                elif d > 0:
                    d = max(int(d*scale), 1)
                delta[i] = d
            super(ydo, self).move(delta[0], delta[1], False)
            npos = self.pos()
            scale *= 0.8
