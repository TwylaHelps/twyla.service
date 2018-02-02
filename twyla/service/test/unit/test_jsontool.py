import datetime
import unittest
import uuid

import twyla.service.jsontool as jsontool


class JSONToolTest(unittest.TestCase):
    def test_simple_json_delegation(self):
        data = {
            "key": "value",
            "nested": {
                "key2": "value2"
            }
        }
        expected = '{"key": "value", "nested": {"key2": "value2"}}'
        assert jsontool.dumps(data) == expected


    def test_uuid_serialization(self):
        data = {
            "uuid": uuid.UUID('67b97d2e-b2b4-43e4-9c50-674c62d11313')
        }
        expected = '{"uuid": "67b97d2e-b2b4-43e4-9c50-674c62d11313"}'
        assert jsontool.dumps(data) == expected


    def test_datetime_serialization(self):
        data = {
            "time": datetime.datetime(2018, 2, 2, 14, 16, 44, 329322)
        }
        expected = '{"time": "2018-02-02T14:16:44.329322"}'
        assert jsontool.dumps(data) == expected


    def test_json_serialization(self):
        class TestObj:
            def __json__(self):
                return 'this is a test'

        data = {
            "obj": TestObj()
        }
        expected = '{"obj": "this is a test"}'
        assert jsontool.dumps(data) == expected
