import sys
import click
from skipper import config
from skipper import cli


def main():
    # pylint: disable=unexpected-keyword-arg
    # pylint: disable=no-value-for-parameter
    # pylint: disable=assignment-from-no-return
    try:
        return_code = cli.cli(
            prog_name='skipper',
            default_map=config.load_defaults(),
            obj={},
            standalone_mode=False
        )
    except click.exceptions.ClickException as exc:
        exc.show()
        return_code = exc.exit_code

    sys.exit(return_code)


if __name__ == '__main__':
    main()
