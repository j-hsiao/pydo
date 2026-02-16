"""Context managers for no mosue acceleration."""
import subprocess as sp

class Gnome(object):
    """Context manager to disable mouse acceleration."""

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


# TODO: how to turn off for other desktop environments?
# TODO: How to detect which desktop environment?
NoAccel = Gnome
