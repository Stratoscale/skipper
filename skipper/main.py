import os
import yaml
from skipper import commands


def _load_defaults():
    skipper_conf = 'skipper.yaml'
    defaults = {}
    if os.path.exists(skipper_conf):
        with open(skipper_conf) as confile:
            config = yaml.load(confile)

        defaults = {
            'registry': config['registry'],
            'image': config['build-container'],
            'tag': 'latest',
            'make': {
                'makefile': config['makefile']
            },
        }

    return defaults


if __name__ == '__main__':
    # pylint: disable=unexpected-keyword-arg
    # pylint: disable=no-value-for-parameter
    commands.cli(
        prog_name='skipper',
        default_map=_load_defaults(),
        obj={}
    )
