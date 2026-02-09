"""Basic ydotool functionality."""
__all__ = ['ydotool', 'ydotoold']
import platform
if platform.system() == 'Windows':
    from .windows import ydotool, ydotoold
else:
    from .linux import ydotool, ydotoold

