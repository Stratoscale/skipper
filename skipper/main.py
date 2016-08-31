import os
import yaml
from skipper import cli


def _load_defaults():
    skipper_conf = 'skipper.yaml'
    defaults = {}
    if os.path.exists(skipper_conf):
        with open(skipper_conf) as confile:
            config = yaml.load(confile)

        defaults = {
            'registry': config['registry'],
            'build_container_image': config['build-container'],
            'build_container_tag': 'latest',
            'make': {
                'makefile': config['makefile']
            },
        }

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
