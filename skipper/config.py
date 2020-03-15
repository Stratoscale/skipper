from string import Template
from collections import defaultdict
import os
import yaml
import six


def load_defaults():
    skipper_conf = 'skipper.yaml'
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
    return Template(key).substitute(defaultdict(lambda: "", os.environ))
