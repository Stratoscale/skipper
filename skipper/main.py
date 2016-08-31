import os
import sys
import yaml
import click
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
    # pylint: disable=assignment-from-no-return
    try:
        return_code = cli.cli(
            prog_name='skipper',
            default_map=_load_defaults(),
            obj={},
            standalone_mode=False
        )
    except click.exceptions.ClickException as exc:
        exc.show()
        return_code = exc.exit_code

    sys.exit(return_code)


if __name__ == '__main__':
    main()
