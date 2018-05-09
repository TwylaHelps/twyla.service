import os
import unittest
from unittest import mock

import pytest


CONF = """
a_key: 'a_value'
"""


import twyla.service.configuration as config


class ConfigurationTest(unittest.TestCase):

    @mock.patch('twyla.service.configuration.os.environ', new={
        'TWYLA_TEST_KEY': 'some-value',
        'TWYLA_TEST_KEY2':  'some-other-value'})
    def test_configuration_from_env(self):
        """
        from_env should read all configurations, and save them with lower and uppercase
        """
        expected = {'test_key': 'some-value',
                    'TEST_KEY': 'some-value',
                    'test_key2': 'some-other-value',
                    'TEST_KEY2': 'some-other-value'}
        conf = config.from_env(prefix='TWYLA_')
        assert conf == expected


    @mock.patch('twyla.service.configuration.os.environ', new={
        'TWYLA_TEST_TEST': 'some-value',
        'TWYLA_TEST2_TEST': 'not-considered'})
    def test_configuration_prefix_without_underscore(self):
        """
        Underscore should be suffixed to the prefix if it's not already there
        """
        expected = {'test': 'some-value', 'TEST': 'some-value'}
        conf = config.from_env(prefix='TWYLA_TEST')
        assert conf == expected

        conf = config.from_env(prefix='TWYLA_TEST_')
        assert conf == expected


    @mock.patch('twyla.service.configuration.os.environ', new={})
    def test_load_config_no_key_set(self):
        with pytest.raises(RuntimeError) as context:
            config.load_config('ENV_KEY')
        assert context.value.args[0] == 'No conf set in environment; set it with key ENV_KEY'


    @mock.patch('twyla.service.configuration.os.environ', new={
        'ENV_KEY': '/file/name.yml',
        'TWYLA_SOME_CONFIG': 'some_config_value'})
    @mock.patch('twyla.service.configuration.open', mock.mock_open(read_data=CONF))
    def test_load_config_prefix_set(self):
        """
        If the env_config_prefix argument is given, the configuration values should
        also be read from the environment
        """
        conf = config.load_config('ENV_KEY', env_config_prefix='TWYLA')
        assert conf == {'a_key': 'a_value',
                        'some_config': 'some_config_value',
                        'SOME_CONFIG': 'some_config_value'}


    @mock.patch('twyla.service.configuration.os.environ', new={
        'ENV_KEY': '/file/name.yml',
        'TWYLA_SOME_CONFIG': 'some_config_value'})
    @mock.patch('twyla.service.configuration.open', mock.mock_open(read_data=CONF))
    def test_load_config_no_prefix(self):
        """
        If the env_config_prefix argument is not given, the configuration values
        should NOT be read from the environment
        """
        conf = config.load_config('ENV_KEY')
        assert conf == {'a_key': 'a_value'}
