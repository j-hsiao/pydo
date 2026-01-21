# pydo
Python wrapper around ydotool + windows version.
This is a tool to allow creating/running macros,
(creating mouse/keyboard inputs).

## Implementation details
On linux, I haven't found a way to directly get mouse position.
As a result, I use tkinter to grab this info.  On windows, the
various windows apis can be used so tk is not needed.
