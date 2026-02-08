import platform
import argparse
if platform.system() == 'Windows':
    from .windows import ydotool, ydotoold
else:
    from .linux import ydotool, ydotoold



def daemon(args):
    """Run the ydotoold daemon."""
    with ydotoold(socket=args.socket, verbose=args.verbose):
        input('Press Return to exit...')


p = argparse.ArgumentParser()
s = p.add_subparsers()

d = s.add_parser('daemon')
d.set_defaults(handler=daemon)
d.add_argument('-s', '--socket')
d.add_argument('-v', '--verbose', action='store_true')

args = p.parse_args()
args.handler(args)
