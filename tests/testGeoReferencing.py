import unittest

from GPSCoord import utm_to_DD

class UTMToDDTests(unittest.TestCase):
    """
    Tests conversion of UTM to latitude longitude in decimal degrees (DD)

    Correct answers obtained using:
    http://www.latlong.net/lat-long-utm.html
    """

    def assertLatLonEqual(self, latlon1, latlon2):
        """
        Handy method for asserting that both latitude and longitude
        are equal. Provide two tuples of (lat, lon).
        Uses assertAlmostEqual to 5 decimal places in attempt to 
        test precision within 1 meter but not within 1/2 of a meter.

        http://en.wikipedia.org/wiki/Decimal_degrees#Precision
        """
        places = 4
        self.assertAlmostEqual(latlon1[0], latlon2[0], places=places)
        self.assertAlmostEqual(latlon1[1], latlon2[1], places=places)

    def testEdmonton(self):
        calculated_latlon = utm_to_DD(348783.31, 5945279.84, 12)
        self.assertLatLonEqual(calculated_latlon, (53.634426, -113.287097))

    def testManitoba(self):
        calculated_latlon = utm_to_DD(552286.59, 5528923.08, 14)
        self.assertLatLonEqual(calculated_latlon, (49.910402, -98.271773))

    def testMaryland(self):
        calculated_latlon = utm_to_DD(378449.42, 4224578.88, 18)
        self.assertLatLonEqual(calculated_latlon, (38.160918, -76.387450))

    def testSydney(self):
        calculated_latlon = utm_to_DD(335918.34, 6253113.37, 56)
        self.assertLatLonEqual(calculated_latlon, ( -33.849525, 151.226451))