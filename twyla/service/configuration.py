import os


def from_env(prefix):
    """If any environment variable starts with prefix, strip it and set
    the value as configuration"""
    from_env = {}

    # Append trailing underscore if it is missing
    if prefix and not prefix.endswith('_'):
        prefix += '_'

    for key, value in os.environ.items():
        if key.startswith(prefix):
            from_env[key.lstrip(prefix).lower()] = value
    return from_env
