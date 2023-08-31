import unittest
from unittest.mock import patch
from datetime import date, datetime, time

from ossdbtoolsservice.driver.types.adapter import InfDateDumper, InfDateLoader, InfTimestampLoader, InfTimeLoader


class TestAdapters(unittest.TestCase):

    def test_InfDateDumper(self):
        with patch.object(InfDateDumper, '__init__', lambda self, cls: None):
            adapter = InfDateDumper(None)
            self.assertEqual(adapter.dump(date.max), b"infinity")
            self.assertEqual(adapter.dump(date.min), b"-infinity")
            self.assertEqual(adapter.dump(date(2021, 1, 1)), b"2021-01-01")

    def test_InfDateLoader(self):
        with patch.object(InfDateLoader, '__init__', lambda self, cls: None):
            adapter = InfDateLoader(None)
            adapter._order = adapter._ORDER_YMD
            self.assertEqual(adapter.load(b"infinity"), date.max)
            self.assertEqual(adapter.load(b"-infinity"), date.min)
            self.assertEqual(adapter.load(b"2000 BC"), date.min)
            self.assertEqual(adapter.load(b"2021-01-01"), date(2021, 1, 1))

    def test_InfTimestampLoader(self):
        with patch.object(InfTimestampLoader, '__init__', lambda self, cls: None):
            adapter = InfTimestampLoader(None)
            adapter._order = adapter._ORDER_YMD
            self.assertEqual(adapter.load(b"infinity"), datetime.max)
            self.assertEqual(adapter.load(b"-infinity"), datetime.min)
            self.assertEqual(adapter.load(b"2000-01-01 BC 12:00:00"), datetime.min)
            self.assertEqual(adapter.load(b"2021-01-01 12:00:00"), datetime(2021, 1, 1, 12, 0))

    def test_InfTimeLoader(self):
        with patch.object(InfTimeLoader, '__init__', lambda self, cls: None):
            adapter = InfTimeLoader(None)
            self.assertEqual(adapter.load(b"24:00:00"), time(0, 0, 0))
            self.assertEqual(adapter.load(b"12:00:00"), time(12, 0, 0))


if __name__ == '__main__':
    unittest.main()
