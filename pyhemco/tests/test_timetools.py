
import unittest
import datetime

from pyhemco import timetools


class TestDatetimeSlicer(unittest.TestCase):

    def setUp(self):
        """Create some datetime slicer examples (valid and invalid)."""
        self.dtslicer1 = {'strp': '2010,2012/1-3/1/0',
                          'args': ([2010, 2012], range(1, 4), [1], [0]),
                          'iter': [(datetime.datetime(2010, 1, 1, 0, 0),
                                    datetime.datetime(2010, 1, 1, 1, 0)),
                                   (datetime.datetime(2010, 2, 1, 0, 0),
                                    datetime.datetime(2010, 2, 1, 1, 0)),
                                   (datetime.datetime(2010, 3, 1, 0, 0),
                                    datetime.datetime(2010, 3, 1, 1, 0)),
                                   (datetime.datetime(2012, 1, 1, 0, 0),
                                    datetime.datetime(2012, 1, 1, 1, 0)),
                                   (datetime.datetime(2012, 2, 1, 0, 0),
                                    datetime.datetime(2012, 2, 1, 1, 0)),
                                   (datetime.datetime(2012, 3, 1, 0, 0),
                                    datetime.datetime(2012, 3, 1, 1, 0))]}

        self.dtslicer2 = {'strp': '2013/6/1,5/*',
                          'args': ([2013], [6], [1, 5], []),
                          'iter': [(datetime.datetime(2013, 6, 1, 0, 0),
                                    datetime.datetime(2013, 6, 2, 0, 0)),
                                   (datetime.datetime(2013, 6, 5, 0, 0),
                                    datetime.datetime(2013, 6, 6, 0, 0))]}

        self.dtslicer3 = {'strp': '2013/*/*/*',
                          'args': ([2013], [], [], []),
                          'iter': [(datetime.datetime(2013, 1, 1, 0, 0),
                                    datetime.datetime(2014, 1, 1, 0, 0))]}

        self.dtslicer4 = {'strp': '2013/*/*/1'}

        self.valid_dtslicers = (self.dtslicer1, self.dtslicer2, self.dtslicer3)
        self.invalid_dtslicers  = (self.dtslicer4,)

    def test_from_string(self):
        """Check string parsing."""
        for dts in self.valid_dtslicers:
            dts_obj1 = timetools.DatetimeSlicer.from_string(dts['strp'])
            dts_obj2 = timetools.DatetimeSlicer(*dts['args'])
            self.assertTrue(dts_obj1.__dict__ == dts_obj2.__dict__)

    def test_to_string(self):
        """Check string conversion."""
        for dts in self.valid_dtslicers:
            self.assertEqual(timetools.DatetimeSlicer(*dts['args']).to_string(),
                             dts['strp'])

    def test__iter__(self):
        """Check iterable."""
        for dts in self.valid_dtslicers:
            self.assertListEqual(list(timetools.DatetimeSlicer(*dts['args'])),
                                 dts['iter'])

    def test_invalid(self):
        """Check if error is returned for invalid string format."""
        for dts in self.invalid_dtslicers:
            with self.assertRaises(ValueError):
                timetools.strp_datetimeslicer(dts['strp'])

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
