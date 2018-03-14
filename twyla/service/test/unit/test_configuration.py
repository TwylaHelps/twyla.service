import os
import unittest
from unittest import mock

import pytest


CONF = """
a_key: 'a_value'
"""


import twyla.service.configuration as config


class ConfigurationTest(unittest.TestCase):
    def test_configuration(self):
        os.environ['TWYLA_TEST_KEY'] = 'some-value'
        os.environ['TWYLA_TEST_KEY2'] = 'some-other-value'
        os.environ['TWYLA_TEST2_KEY2'] = 'not-considered'

        prefixes = ['TWYLA_TEST', 'TWYLA_TEST_']
        expected = {'key': 'some-value',
                    'key2': 'some-other-value'}

        for prefix in prefixes:
            conf = config.from_env(prefix=prefix)
            assert conf == expected

        # cleanup
        del os.environ['TWYLA_TEST_KEY']
        del os.environ['TWYLA_TEST_KEY2']
        del os.environ['TWYLA_TEST2_KEY2']


    def test_configuration_prefix_eq_key(self):
        """
        This was added due to a bug where lstrip was used
        """
        os.environ['TWYLA_TEST_TEST'] = 'some-value'
        os.environ['TWYLA_TEST2_TEST'] = 'not-considered'

        prefixes = ['TWYLA_TEST', 'TWYLA_TEST_']
        expected = {'test': 'some-value'}

        for prefix in prefixes:
            conf = config.from_env(prefix=prefix)
            assert conf == expected

        del os.environ['TWYLA_TEST_TEST']
        del os.environ['TWYLA_TEST2_TEST']


    @mock.patch('twyla.service.configuration.os.environ', new={})
    def test_load_config_no_key_set(self):
        with pytest.raises(RuntimeError) as context:
            config.load_config('ENV_KEY')
        assert context.value.args[0] == 'No conf set in environment; set it with key ENV_KEY'


    @mock.patch('twyla.service.configuration.os.environ',
                new={'ENV_KEY': '/file/name.yml',
                     'TWYLA_SOME_CONFIG': 'some_config_value'})
    @mock.patch('twyla.service.configuration.open', mock.mock_open(read_data=CONF))
    def test_load_config(self):
        conf = config.load_config('ENV_KEY')
        assert conf == {'a_key': 'a_value',
                        'SOME_CONFIG': 'some_config_value'}


    @mock.patch('twyla.service.configuration.os.environ',
                new={'ENV_KEY': '/file/name.yml'})
    @mock.patch('twyla.service.configuration.open', mock.mock_open(read_data=CONF))
    def test_load_config_keys_from_env(self):
        conf = config.load_config('ENV_KEY')
        assert conf == {'a_key': 'a_value'}
