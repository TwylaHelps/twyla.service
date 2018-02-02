import os
import unittest

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
