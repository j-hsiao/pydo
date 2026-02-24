"""Observations:

NOTE: these observations are difficult to check on wsl because
      wsl doesn't actually have any /dev/uinput so ydotool does
      not work.

1. winfo pointerxy is updated without processing any new events.

   O    windows
   O    wayland(arch)
   ?    wayland(wsl)
   ?    Xvnc(arch)
   ?    Xvnc(wsl)
2. During the callback, even with update(), if exiting fullscreen and
   then changing geometry to be smaller, <Motion> events are no longer
   or less frequently fired if the mouse is not inside the window.

   O    windows
   O    wayland(arch)
   ?    wayland(wsl)
   ?    Xvnc(arch)
   ?    Xvnc(wsl)

3. update() followed by click down is good enough to click into the
   application and capture mouse focus.  No need to detect
   whether <Motion> or <Enter> indicates that the fullscreen
   window is ready for the mouse to click into the application for
   captured mouse focus.

   O    windows
   X    wayland(arch)
   ?    wayland(wsl)
   ?    Xvnc(arch)
   ?    Xvnc(wsl)

"""
import tkinter as tk
import time
import sys
sys.path.insert(0, '.')
from pydo.ydotool import ydotool
import argparse

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-u', '--update', action='store_true')
    p.add_argument('-f', '--fullscreen', action='store_true')
    p.add_argument('-v', '--variable', action='store_true')
    p.add_argument('-i', '--idle', help='idle_tasks', action='store_true')
    args = p.parse_args()

    with ydotool(daemon=True) as y:
        def moved(x, y):
            print('<Motion>', x, y, time.time())

        def move():
            r.geometry('0x0+0+0')
            r.attributes('-fullscreen', True, '-topmost', True)
            r.update()
            r.call('set', 'mydumyvar', '0')
            r.call('after', 500, 'set mydumyvar 0')
            r.call('vwait', 'mydumyvar')
            y.click(y.m.LEFT|y.m.DOWN)
            try:
                print('?', time.time())
                print(0, r.winfo_pointerxy(), time.time())
                for i in range(10):
                    y.move_(1, 1, absolute=False)
                    if args.update:
                        r.update()
                    elif args.idle:
                        r.update_idletasks()
                    print(i+1, r.winfo_pointerxy(), time.time())
            finally:
                y.click(y.m.LEFT|y.m.UP)
                if args.fullscreen:
                    r.attributes('-fullscreen', False)
                    r.geometry('200x200+0+0')


        r = tk.Tk()
        tkv = tk.BooleanVar(r)
        r.createcommand('mymoved', moved)
        r.createcommand('mymove', move)
        r.bind('<Motion>', 'mymoved %X %Y')
        r.bind('<space>', 'mymove')
        r.bind('<Button-1>', 'puts "clicked"')

        if not args.fullscreen:
            r.bind('<Button-1>', 'puts "clicked"\nwm attributes . -fullscreen False\nwm geometry . 200x200+0+0')

        if args.variable:
            r.bind('<Escape>', 'set {} true'.format(tkv))
            r.call('vwait', tkv)
        else:
            r.bind('<Escape>', 'destroy {}'.format(r))
            r.mainloop()
