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
    'configs': -1,
    'enters': set(),
    'exits': set(),
    'cur': []
}

def name(f):
    return f'pyfunc_{f.__name__}'
def reset(v=0):
    if v >= 0:
        print('\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    else:
        print('\n<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    state['configs'] = v
    state['cur'] = []

def check(*nargs):
    if args.withdraw:
        if nargs:
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
            if state['cur'] and state['enters']:
                state['exits'].add(''.join(state['cur']))
            r.withdraw()
            r.call('after', '1000', '{} 3'.format(name(check)))
    else:
        if state['cur'] and state['enters']:
            state['exits'].add(''.join(state['cur']))
        if args.before:
            reset()
        r.attributes('-fullscreen', True, '-topmost', True)
        if args.update:
            r.update()
        if not args.before:
            reset()


def on_config():
    state['cur'].append('C')
    print('c', end='', flush=True)
    if state['configs'] >= 0:
        state['configs'] += 1
    else:
        state['configs'] -= 1

def on_enter(x, y, s):
    if state['configs'] >= 0:
        state['cur'].append('E')
        print('e', end='', flush=True)
        if args.coord:
            print('({},({},{}),{})'.format(state['configs'], x, y, '{:0b}'.format(int(s))), end='', flush=True, file=sys.stderr)

def on_motion(x, y, s):
    if state['configs'] >= 0:
        state['cur'].append('M')
        print('m', end='', flush=True)
        if args.coord:
            print('({},({},{}),{})'.format(state['configs'], x, y, '{:0b}'.format(int(s))), end='', flush=True, file=sys.stderr)

def on_click():
    if state['cur']:
        state['enters'].add(''.join(state['cur']))
    if args.before:
        reset(-1)
    r.attributes('-fullscreen', False)
    if args.update:
        r.update()
    if not args.before:
        reset(-1)

def on_leave():
    print('L',  end='', flush=True)
    state['cur'].append('L')
    if args.coord:
        print('({})'.format(state['configs']), end='', flush=True, file=sys.stderr)

for item in check, on_config, on_motion, on_enter, on_click, on_leave:
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
r.bind('<ButtonRelease-1>', name(on_click))
r.bind('<Leave>', name(on_leave))

r.mainloop()
print()

print('enterring:')
for item in state['enters']:
    print(item)
print('exiting:')
for item in state['exits']:
    print(item)
