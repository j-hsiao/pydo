import argparse
from pydo import ydo

def handle_type(args):
    with ydo(server=not args.noserver) as y:
        y.type(*args.strings, keydelay = args.key_delay, nextdelay=args.next_delay)

def handle_server(args):
    with ydo(server=True) as y:
        input('Press return to exit.')

p = argparse.ArgumentParser()
p.add_argument('-n', '--noserver', help='no ydo server.', action='store_true')
sub = p.add_subparsers()

sp = sub.add_parser('serve')
sp.set_defaults(func=handle_server)

tp = sub.add_parser('type')
tp.set_defaults(func=handle_type)
tp.add_argument('strings', nargs='*', help='strings to type.')
tp.add_argument('--key-delay', type=int, default=12, help='delay between key events (msec)')
tp.add_argument('--next-delay', type=int, default=0, help='delay between strings (msec)')

args = p.parse_args()
args.func(args)
