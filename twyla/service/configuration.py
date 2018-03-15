import os
import yaml

def from_env(prefix):
    """If any environment variable starts with prefix, strip it and set
    the value as configuration"""
    from_env = {}

    # Append trailing underscore if it is missing
    if prefix and not prefix.endswith('_'):
        prefix += '_'

    for key, value in os.environ.items():
        if key.startswith(prefix):
            from_env[key[len(prefix):].lower()] = value
    return from_env


def config_from_env(prefix):
    """If any environment variable starts with prefix, strip it and set
    the value as configuration"""
    from_env = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            from_env[key.lstrip(prefix)] = value
    return from_env


def load_config(env_key):
    try:
        conf_file = os.environ[env_key]
    except KeyError:
        err = 'No conf set in environment; set it with key {}'.format(env_key)
        raise RuntimeError(err) from None
    with open(conf_file, 'r') as conf_file:
        configuration = yaml.load(conf_file.read())
    configuration.update(config_from_env('TWYLA_'))
    return configuration

