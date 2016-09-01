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
            normalized_config[normalized_key] = value
