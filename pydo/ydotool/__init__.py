"""Basic ydotool functionality."""
import platform
if platform.system() == 'Windows':
    from .windows import ydotool
else:
    from .linux import ydotool

