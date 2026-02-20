"""Gather observations on when a fullscren tk window is ready

Update() does not seem to be enough on some systems (usually
where X is involved on a non-X system...)


withdraw -> fullscreen topmost -> deiconify


enterring exiting sequences
update  withdraw    geom    before  windows     wsl         Xvnc        wayland(arch)
n       n           0       n       CC  CC      CCCEM  CLCC             CCCEM   CLCC
                                    CCE CCL     CCCEMM                  CCECM
n       n           0       y       CCE CCL     CCCEM CLCC              CCCEM   CLCC
                                                CCECM                   CCECM
n       y           0       n       CE  CCL     CELCECM                 EM      CLCC
                                                CCECM CLCC
n       y           0       y       CE  CCL     CCCECM CLCC             CCEM    CLCC
                                                CCCELCECM               CCCEM
y       n           0       n       n/a n/a     M     C                 CCCEM   CLCC
                                                EM    CLCC
                                                CCCEM
y       n           0       y       CCE CCL     CCCEM CLCC              CCECM   CLCC
                                    CC  CC                              CCCEM
y       y           0       n       MMM L       LCECMMMM                EM      CLCC
                                                ECM      C
y       y           0       y       CE  CCL     CCCECM CLCC             CCCEM   CLCC
                                                CCCELCECM
"""
import argparse
import sys
import tkinter as tk

r = tk.Tk()
r.geometry('50x50+5+5')
r.attributes('-topmost', True)
state = {
    'cap': False,
    'enter': set(),
    'leave': set(),
    'cur': [],
    'mode': 'enter',
}

def epush(ev):
    """Print an event."""
    state['cur'].append(ev)
    print(ev, end='', flush=True)

def coords(x, y, s):
    """Print coordinates and info.

    x,y: current (root) coordinates
    s: state bitflags
    """
    if args.coord:
        print('({}, ({},{}), {})'.format(
            len([_ for _ in state['cur'] if _ == 'C']),
            x, y, '{:0b}'.format(int(s)),
            flush=True, file=sys.stderr))

def name(f):
    return f'pyfunc_{f.__name__}'
def reset(v=0):
    if v >= 0:
        print('Enter: ', end='', flush=True)
    else:
        print('Leave: ', end='', flush=True)
    state['cap'] = True
    state['cur'] = []

def commit():
    if state['cap']:
        state['cap'] = False
        state[state['mode']].add(''.join(state['cur']))
        print()
        if state['mode'] == 'enter':
            state['mode'] = 'leave'
        else:
            state['mode'] = 'enter'

def on_config():
    if state['cap']:
        epush('C')

def on_enter(x, y, s):
    if state['cap']:
        epush('E')
        coords(x, y, s)

def on_motion(x, y, s):
    if state['cap']:
        epush('M')
        coords(x, y, s)

def on_leave(x, y, s):
    if state['cap']:
        epush('L')
        coords(x, y, s)

def check():
    commit()
    if args.withdraw:
        if state['mode'] == 'enter':
            if r.state() == 'withdrawn':
                if args.before:
                    reset()
                if args.size[0] >= 0:
                    r.geometry('{}x{}+5+5'.format(*args.size))
                r.attributes('-fullscreen', True, '-topmost', True)
                r.deiconify()
                if args.update:
                    r.update()
                if not args.before:
                    reset()
            else:
                r.withdraw()
                r.call('after', '1000', name(check))
        else:
            r.call(
                'after', '1000',
                '{}\nwm attributes {} -fullscreen false\nwm geometry {} 50x50+5+5\nwm deiconify {}'.format(
                    name(commit), r, r, r))
            if args.before:
                reset()
            r.withdraw()
            if args.update:
                r.update()
            if not args.before:
                reset()
    else:
        if args.before:
            reset()
        if state['mode'] == 'enter':
            r.attributes('-fullscreen', True, '-topmost', True)
        else:
            r.attributes('-fullscreen', False)
        if args.update:
            r.update()
        if not args.before:
            reset()




for item in check, on_config, on_motion, on_enter, on_leave, commit:
    r.createcommand(name(item), item)

p = argparse.ArgumentParser()
p.add_argument('-u', '--update', action='store_true')
p.add_argument('-w', '--withdraw', help='withdraw before check', action='store_true')
p.add_argument('-s', '--size', nargs='*', type=int, default=[0])
p.add_argument('-b', '--before', help='Reset number of <Configure> before any changes', action='store_true')

p.add_argument('-c', '--coord', help='print coord states', action='store_true')
args = p.parse_args()
if len(args.size) == 1:
    args.size.append(args.size[0])

r.bind('<space>', name(check))
r.bind('<Escape>', f'destroy {r}')
r.bind('<Enter>', '{} %X %Y %s'.format(name(on_enter)))
r.bind('<Motion>', '{} %X %Y %s'.format(name(on_motion)))
r.bind('<Configure>', name(on_config))
r.bind('<Leave>', '{} %X %Y %s'.format(name(on_leave)))

r.mainloop()
print()

for item in 'enter', 'leave':
    print(item)
    for x in state[item]:
        print(x)
