import unittest
from unittest.mock import patch

from station import GroundStation

@patch("station.UI") # See http://www.voidspace.org.uk/python/mock/patch.html#where-to-patch
class StationTestCase(unittest.TestCase):
    def testRuns(self, patched_UI):
        """
        Tests that the program runs without crashing. The UI is mocked
        out to prevent a window from showing and the test from never
        finishing.
        """
        ground_station = GroundStation()
        ground_station.run()
