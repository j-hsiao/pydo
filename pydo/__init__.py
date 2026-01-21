import platform
if platform.system() == 'Windows':
    from pydo.platform.windows import ydo
else:
    from pydo.platform.linux import ydo
