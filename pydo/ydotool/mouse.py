class Mouse(object):
    # On Arch Wayland, these correspond to: 1, 3, 2, 8, 9, 10, 11, 12
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
    DOWNUP = DOWN | UP
