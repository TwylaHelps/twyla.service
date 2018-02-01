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
