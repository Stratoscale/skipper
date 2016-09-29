from string import Template
from collections import defaultdict
import os
import yaml


def load_defaults():
    skipper_conf = 'skipper.yaml'
    defaults = {}
    if os.path.exists(skipper_conf):
        with open(skipper_conf) as confile:
            config = yaml.load(confile)
        _normalize_config(config, defaults)

    return defaults


def _normalize_config(config, normalized_config):
    for key, value in config.iteritems():
        if isinstance(value, dict):
            normalized_config[key] = {}
            _normalize_config(value, normalized_config[key])
        else:
            normalized_key = key.replace('-', '_')
            normalized_config[normalized_key] = _interpolate_env_vars(value)


def _interpolate_env_vars(key):
    return Template(key).substitute(defaultdict(lambda: "", os.environ))
