import tkinter as tk
import time
from pydo.ydotool import ydotool



with ydotool() as y:
    def moved():
        print('!', time.time())

    def move():
        print('?', time.time())
        for i in range(10):
            y.move_(5, 5, absolute=False)
            print(i, r.winfo_pointerxy())

    r = tk.Tk()
    tkv = tk.BooleanVar(r)
    r.createcommand('mymoved', moved)
    r.createcommand('mymove', move)
    r.bind('<Motion>', 'mymoved')
    r.bind('<space>', 'mymove')

    r.bind('<Escape>', 'set {} true'.format(tkv))
    r.call('vwait', tkv)

    # r.bind('<Escape>', 'destroy {}'.format(r))
    # r.mainloop()
