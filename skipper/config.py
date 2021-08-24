import os
from collections import defaultdict
from re import findall
from string import Template
from subprocess import check_output

import six
import yaml


def load_defaults():
    skipper_conf = os.environ.get('SKIPPER_CONF', 'skipper.yaml')

    defaults = {}
    if os.path.exists(skipper_conf):
        with open(skipper_conf) as confile:
            config = yaml.safe_load(confile)
            containers = config.pop('containers', None)
        _normalize_config(config, defaults)
        if containers is not None:
            defaults['containers'] = containers
    return defaults


def _normalize_config(config, normalized_config):
    for key, value in six.iteritems(config):
        if isinstance(value, dict):
            normalized_config[key] = {}
            _normalize_config(value, normalized_config[key])
        elif isinstance(value, list):
            normalized_config[key] = [_interpolate_env_vars(x) for x in value]
        else:
            normalized_key = key.replace('-', '_')
            normalized_config[normalized_key] = _interpolate_env_vars(value)


def _interpolate_env_vars(key):
    for match in findall(r'\$\(.+\)', key):
        output = check_output("echo " + match, shell=True).strip().decode("utf-8")
        if not output:
            raise ValueError(match)
        key = key.replace(match, output)
    return Template(key).substitute(defaultdict(lambda: "", os.environ))
