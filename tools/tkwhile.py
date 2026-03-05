"""Test if a while loop is a work around slow callbacks.


Observations:
wayland(arch)
    holding middle button in window keeps mouse focus.
    However, left clicking in this state will still cause other
    windows to gain focus.  keypresses are not detected in this
    state, but botton clicks are.
    However, click+dragging does not seem to work.
"""

import argparse
import tkinter as tk
import textwrap
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pydo import ydotool

p = argparse.ArgumentParser()
p.add_argument('-f', '--fullscreen', action='store_true')
args = p.parse_args()

with ydotool.ydotool(daemon=True) as ydo:
    r = tk.Tk()
    middown = [False]
    def toggle_middle(*args):
        if middown[0]:
            ydo.click(ydo.m.MIDDLE|ydo.m.UP)
            middown[0] = False
            print('mid up')
        elif not args:
            ydo.click(ydo.m.MIDDLE|ydo.m.DOWN)
            middown[0] = True
            print('mid down')

    def relmo(x, y):
        ydo.move(int(x), int(y), absolute=False)

    if args.fullscreen:
        r.attributes('-fullscreen', True, '-topmost', True)
        cm = ''
    else:
        cm = '#'

    r.createcommand('pyfunc_relmo', relmo)
    r.createcommand('pyfunc_toggle_middle', toggle_middle)
    r.bind(
        '<Button-2>',
        textwrap.dedent(
            f'''{cm}wm attributes {r} -fullscreen false
            wm geometry {r} 200x200+[expr [winfo screenwidth {r}]/2]+[expr [winfo screenheight {r}]/2]
            '''
        ))
    r.bind('<ButtonRelease-2>', f'{cm}wm attributes {r} -fullscreen true')

    r.bind(
        '<ButtonRelease-3>',
        textwrap.dedent(f'''
        puts "start moving?"
        puts "[winfo pointerxy {r}]"
        while {{"[winfo pointerxy {r}]" != "0 0"}} {{
            puts "[winfo pointerxy {r}]"
            pyfunc_relmo -1 -1
            update
        }}
        puts "done moving?"''')
    )
    print(r.bind('<ButtonRelease-3>'))

    r.bind('<Control-space>', 'pyfunc_toggle_middle')

    r.bind('<ButtonPress>', 'puts "<Button-%b>"')
    r.bind('<ButtonRelease>', 'puts "<ButtonRelease-%b>"')

    r.bind('<KeyPress>', 'puts "<Key-%K>"')
    r.bind('<KeyRelease>', 'puts "<KeyRelease-%K>"')

    r.bind('<Motion>', 'puts "<Motion> %X %Y"')
    r.bind('<B2-Motion>', 'puts "<B2-Motion> %X %Y"')
    r.bind('<B1-Motion>', 'puts "<B1-Motion> %X %Y"')
    r.bind('<B1-B2-Motion>', 'puts "<B1-B2-Motion> %X %Y"')

    r.bind('<F7>', 'puts "<F7>"')

    r.bind('<Escape>', f'destroy {r}')
    r.bind('<B2-Escape>', f'pyfunc_toggle_middle off\nupdate\ndestroy {r}')
    r.mainloop()
