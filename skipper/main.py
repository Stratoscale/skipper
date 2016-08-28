import os
import yaml
from skipper import commands


def _load_defaults():
    defaults = {}
    if os.path.exists('skipper.yaml'):
        with open('skipper.yaml') as confile:
            config = yaml.load(confile)

        defaults = {
            'build': {
                'registry': config['registry'],
            },
            'run': {
                'registry': config['registry'],
                'image': config['build-container'],
                'tag': 'latest',
            },
            'make': {
                'registry': config['registry'],
                'image': config['build-container'],
                'tag': 'latest',
                'makefile': config['makefile']
            },
        }

    return defaults


if __name__ == '__main__':
    # pylint: disable=unexpected-keyword-arg
    # pylint: disable=no-value-for-parameter
    commands.cli(
        prog_name='skipper',
        default_map=_load_defaults()
    )
