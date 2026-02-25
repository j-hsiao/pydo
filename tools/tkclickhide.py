"""Check various methods of moving window out of the way when dragging...

1. normal window, make small and move to a corner
    win: normal
    wsl: normal
    Xvnc(wsl): normal
    Xvnc(arch):
    way(arch):

2. fullscreen, turn into window and move to corner
    win: motion events are slow if mouse is not inside the window.
    wsl: normal
    Xvnc(wsl): normal
    Xvnc(arch):
    way(arch):

3. fullscreen, withdraw, then deiconify on release
    win: motion events are slow, but button release is responsive
    wsl: no response after withdraw
    Xvnc(wsl): no response after withdraw
    Xvnc(arch):
    way(arch):

4. fullscreen, turn into window and keep window underneath the cursor.
    win: normal (unless mouse moves too fast and exits window, then it lags)
    wsl: normal (but cursor is on menubar instead of middle of window...)
    Xvnc(wsl): normal (but cursor is on menubar instead of middle of window...)
    Xvnc(arch):
    way(arch):
"""
import tkinter as tk
r = tk.Tk()
r.bind('<Motion>', 'puts "Motion! %X %Y %t"')
r.bind('<ButtonPress-1>', f'wm geometry {r} 200x200+0+0')
r.bind('<ButtonRelease-1>', f'wm geometry {r} 200x200+860+500')
r.bind('<Escape>', f'destroy {r}')
r.mainloop()

r = tk.Tk()
r.attributes('-fullscreen', True, '-topmost', True)
r.bind('<Motion>', 'puts "Motion! %X %Y %t"')
r.bind('<ButtonPress-1>', f'wm attributes {r} -fullscreen false\nwm geometry {r} 200x200+0+0')
r.bind('<ButtonRelease-1>', f'wm attributes {r} -fullscreen true')
r.bind('<Escape>', f'destroy {r}')
r.mainloop()

r = tk.Tk()
r.attributes('-fullscreen', True, '-topmost', True)
r.bind('<Motion>', 'puts "Motion! %X %Y %t"')
r.bind('<ButtonPress-1>', f'wm withdraw {r}\nafter 5000 "puts \\"Via after\\"\\nwm deiconify {r}\\nwm attributes {r} -fullscreen true -topmost true"')
r.bind('<ButtonRelease-1>', f'puts "via button release"\nwm deiconify {r}\nwm attributes {r} -fullscreen true -topmost true')
r.bind('<Escape>', f'destroy {r}')
r.mainloop()

r = tk.Tk()
r.attributes('-fullscreen', True, '-topmost', True)
r.bind('<Motion>', f'puts "Motion! %X %Y %t %w %h"\n')
r.bind('<Button-1>', f'wm attributes {r} -fullscreen false\nwm geometry {r} 120x60+[expr [winfo x {r}]+%x-60]+[expr [winfo y {r}] + %y-30]')
r.bind('<B1-Motion>', f'puts "dragged motion %X %Y %t [winfo x {r}] [winfo y {r}]"\nwm geometry {r} 120x60+[expr [winfo x {r}]+%x-60]+[expr [winfo y {r}] + %y-30]')
r.bind('<ButtonRelease-1>', f'wm attributes {r} -fullscreen true')
r.bind('<Escape>', f'destroy {r}')
r.mainloop()
