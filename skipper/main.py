import argparse
import logging
import os
import yaml
from skipper import commands


DEFAULT_REGISTRY = 'rackattack-nas.dc1:5000'
DEFAULT_TAG = 'latest'
DEFAULT_CONFIG_FILE = 'skipper.yaml'


def load_config():
    config = {}
    if os.path.exists(DEFAULT_CONFIG_FILE):
        config = yaml.load(open(DEFAULT_CONFIG_FILE))

    return config


def parse_args(config):
    parser = argparse.ArgumentParser(prog='skipper',
                                     description='Easily dockerize your Git repository',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--registry', default=DEFAULT_REGISTRY, help='url of the docker registry')
    parser.add_argument('--image', default=config.get('build-container'), help='image to use for running commands')
    parser.add_argument('--tag', default=DEFAULT_TAG, help='tag of the image to use')
    parser.add_argument('-e', '--env', action='append', help='set environment variables')
    parser.add_argument('-q', '--quiet', action='store_true', help='silence output')

    subparsers = parser.add_subparsers(dest='subparser_name')

    parser_build = subparsers.add_parser('build', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_build.add_argument('--image', required=True, help='image name')
    parser_build.add_argument('--tag', default=DEFAULT_TAG, help='image tag')

    parser_run = subparsers.add_parser('run', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_run.add_argument('command', nargs=argparse.REMAINDER)

    parser_make = subparsers.add_parser('make', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_make.add_argument('-f', '--file', default=config.get('makefile', 'Makefile'), help='path to the makefile')
    parser_make.add_argument('target', nargs=argparse.REMAINDER)

    parser_make = subparsers.add_parser('depscheck', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_make.add_argument('-f', '--file', help='path to the manifesto')

    return parser.parse_args()


def main():
    config = load_config()
    args = parse_args(config)

    logging_level = logging.INFO if args.quiet else logging.DEBUG
    logging.basicConfig(format='%(message)s', level=logging_level)

    if args.subparser_name == 'run':
        commands.run(args.registry, args.image, args.tag, args.env, args.command)

    elif args.subparser_name == 'build':
        dockerfile = args.image + '.Dockerfile'
        commands.build(args.registry, args.image, dockerfile, args.tag)

    elif args.subparser_name == 'make':
        commands.make(args.registry, args.image, args.tag, args.env, args.file, args.target[0])

    elif args.subparser_name == 'depscheck':
        commands.depscheck(args.registry, args.image, args.tag, args.file)


if __name__ == '__main__':
    main()
