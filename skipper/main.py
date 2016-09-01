import os
import yaml
from skipper import cli


def _load_defaults():
    skipper_conf = 'skipper.yaml'
    defaults = {}
    if os.path.exists(skipper_conf):
        with open(skipper_conf) as confile:
            defaults = yaml.load(confile)

    return defaults


def main():
    # pylint: disable=unexpected-keyword-arg
    # pylint: disable=no-value-for-parameter
    cli.cli(
        prog_name='skipper',
        default_map=_load_defaults(),
        obj={}
    )


if __name__ == '__main__':
    main()
