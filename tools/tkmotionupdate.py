"""

windows: update() seems 100% always wait until after <Motion>
XWayland(Arch): <Motion> is sometimes after update() returns.
Using only 'after idle', <Motion> is almost always afterwards.
using 'after 1', <Motion> is almost always before, but still sometimes after


"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pydo import ydotool
import time
import tkinter as tk
with ydotool.ydotool(daemon=True) as ydo:
    r = tk.Tk()
    r.geometry('{}x{}+0+0'.format(int(r.winfo_screenwidth()*0.6), r.winfo_screenheight()))
    count = [0]
    times = []
    def moveit(x,y):
        print('begin motion')
        ydo.move(50,50,False)
        # r.update()
        # print('  updated', r.winfo_pointerxy())
        r.call('after', 1, '  puts "I am now idle"')



        # x, y = int(x), int(y)
        # tx = 960
        # ty = 540
        # if x != tx or y != ty:
        #     delta = []
        #     for c, t in ((x, tx), (y, ty)):
        #         if c < t:
        #             delta.append(1)
        #         elif c > t:
        #             delta.append(-1)
        #         else:
        #             delta.append(0)
        #     r.call('set', 'pyvar_motioned', '0')
        #     ydo.move(delta[0], delta[1], False)
        #     times.append(time.time())
        #     r.update()
        #     r.call('after', 'idle', 'pyfunc__moveit $pyvar_x $pyvar_y')
        #     if not r.call('expr', '$pyvar_motioned'):
        #         print('no motion before updated.')
        # else:
        #     print('reached', count[0])
        #     count[0] += 1
        #     tdeltas = [t2-t1 for t1, t2 in zip(times[:-1], times[1:])]
        #     print('number of motions:', len(tdeltas))
        #     print('  min:', min(tdeltas))
        #     print('  max:', max(tdeltas))
        #     print('  avg:', sum(tdeltas) / len(tdeltas))
        #     del times[:]

    r.createcommand('pyfunc__moveit', moveit)
    r.bind('<space>', 'pyfunc__moveit %X %Y')
    r.bind('<Motion>', 'puts "  <Motion> %X %Y"\nset pyvar_x %X\nset pyvar_y %Y\nset pyvar_motioned 1')
    r.bind('<Escape>', f'destroy {r}')
    r.mainloop()
