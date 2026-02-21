"""Gather observations on when a fullscren tk window is ready

sidenotes:
    withdrawing/deiconify seems to be the best option in general
    because the deiconify step ensures the window will end up on top
    of all the others whereas sometimes, for XWayland(arch or wsl)
    sometimes, topmost is still below other non-topmost non-xwayland
    windows.  This also has the benefit of more consistent results.

    wsl case maybe doesn't matter? pydo wouldn't work with it anyways
    and since wsl is on windows, just use the windows version...

cases:
    wubs:
        withdraw(y/n): withdraw or just exit/enter full screen
        update(y/n): call update() after changing state.
        before(y/n): start recording before or after changing state.
        s(int), size, change geometry before deiconify if applicable.

withdraw(y/n) update(y/n) before(y/n)
yyy0
    XWayland
        enter: CCCEM CCEM
        leave: LC
    Xvnc (wayland)
        enter: CCCCE
        leave: L
    wsl
        enter: CCCECMCM CCCECMCLEM CCCELCECM
        leave: L
    win
        enter: CE
        leave: L
In this case, 1 or 4 C before E implies no M

yyn0
    win
        enter:
        leave: L
    wsl
        enter: LCECM CCECMCLEM CMCLEM
        leave:
    Xwayland
        enter: EM
        leave:
    Xvnc (wayland)
        enter:
        leave:
win and Xvnc don't even have Enter registered, (update causes the
enter to happen before starting recording?)
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
            x, y, '{:0b}'.format(int(s))),
            flush=True, file=sys.stderr, end='')

def name(f):
    return f'pyfunc_{f.__name__}'
def reset():
    if state['mode'] == 'enter':
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

def toggle_coord():
    args.coord = not args.coord
    print(args.coord)
def print_seqs():
    """Commit and print current sequences."""
    commit()
    if state['enter'] or state['leave']:
        print('------------------------------')
        for item in 'enter', 'leave':
            print(f'{item}:', *state[item])
        state['enter'] = set()
        state['leave'] = set()

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




for item in (
    check,
    on_config,
    on_motion,
    on_enter,
    on_leave,
    commit,
    print_seqs,
    toggle_coord,
):
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
r.bind('<e>', name(commit))
r.bind('<p>', name(print_seqs))
r.bind('<c>', name(toggle_coord))

r.mainloop()
print_seqs()
