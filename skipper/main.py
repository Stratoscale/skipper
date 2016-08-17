from skipper import commands
import argparse
import logging


DEFAULT_REGISTRY = 'rackattack-nas.dc1:5000'
DEFAULT_IMAGE = 'dev-base'
DEFAULT_TAG = 'latest'
DEFAULT_CONFIG_FILE = 'skipper.yaml'

def parse_args():
    parser = argparse.ArgumentParser(prog='skipper',
                                     description='Easily dockerize your Git repository',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--config-file', default=DEFAULT_CONFIG_FILE, help='path to the configuration file')
    parser.add_argument('--registry', default=DEFAULT_REGISTRY, help='url of the docker registry')
    parser.add_argument('--image', default=DEFAULT_IMAGE, help='image to use for running commands')
    parser.add_argument('--tag', default=DEFAULT_TAG, help='tag of the image to use')
    parser.add_argument('-v', '--verbose', action='store_true', help='increase verbosity')

    subparsers = parser.add_subparsers(dest='subparser_name')

    parser_build = subparsers.add_parser('build')
    parser_build.add_argument('-f', '--file', default='Dockerfile', help='path to the dockerfile')

    parser_run = subparsers.add_parser('run')
    parser_run.add_argument('command', nargs=argparse.REMAINDER)

    parser_make = subparsers.add_parser('make')
    parser_make.add_argument('-f', '--file', default='Makefile', help='path to the makefile')
    parser_make.add_argument('target', nargs=argparse.REMAINDER)

    parser_make = subparsers.add_parser('depscheck')
    parser_make.add_argument('-f', '--file', help='path to the manifesto')

    return parser.parse_args()
def main():
    args = parse_args() 

    logging_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format='%(message)s', level=logging_level)

    if args.subparser_name == 'run':
        commands.run(args.registry, args.image, args.tag, args.command)

    elif args.subparser_name == 'build':
        commands.build(args.registry, args.image, args.file)

    elif args.subparser_name == 'make':
        commands.make(args.registry, args.image, args.tag, args.file, args.target[0])

    elif args.subparser_name == 'depscheck':
        output = commands.depscheck(args.registry, args.image, args.tag, args.file)


if __name__ == '__main__':
    main()
