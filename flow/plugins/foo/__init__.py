from flow.plugins.foo.foo import Foo

parser = 'foo'

def register_parser(new_parser):
    new_parser.add_argument('action', help='Action to take, possible values: bar, baz')
    new_parser.add_argument('-v', '--version', help='Version to use')


def run_action(args):
    foo_instance = Foo()

    if args.action == 'fooa':
        foo_instance.bar()
    elif args.action == 'foob':
        foo_instance.baz()
