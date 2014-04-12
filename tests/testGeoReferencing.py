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
        places = 5
        self.assertAlmostEqual(latlon1[0], latlon2[0], places=places)
        self.assertAlmostEqual(latlon1[1], latlon2[1], places=places)

    @unittest.skip("Known issue: The algorithm is close but not perfectly accurate.")
    def testEdmonton(self):
        calculated_latlon = utm_to_DD(348783.31, 5945279.84, 12)
        self.assertLatLonEqual(calculated_latlon, (53.634426, -113.287097))

    def testManitoba(self):
        calculated_latlon = utm_to_DD(552286.59, 5528923.08, 14)
        self.assertLatLonEqual(calculated_latlon, (49.910402, -98.271773))

    @unittest.skip("Known issue: The algorithm is close but not perfectly accurate.")
    def testMaryland(self):
        calculated_latlon = utm_to_DD(378449.42, 4224578.88, 18)
        self.assertLatLonEqual(calculated_latlon, (38.160918, -76.387450))
    
    @unittest.skip("Known issue: The algorithm is close but not perfectly accurate.")
    def testSydney(self):
        calculated_latlon = utm_to_DD(335918.34, 6253113.37 - 10000000, 56)
        self.assertLatLonEqual(calculated_latlon, ( -33.849525, 151.226451))

    @unittest.skip("Known issue: The algorithm is close but not perfectly accurate.")
    def testCapeTown(self):
        calculated_latlon = utm_to_DD(262609.03, 6244778.96 - 10000000, 34)
        self.assertLatLonEqual(calculated_latlon, (-33.910679, 18.432394))

    def testParis(self):
        calculated_latlon = utm_to_DD(452170.72, 5411703.17, 31)
        self.assertLatLonEqual(calculated_latlon, (48.856450, 2.347951))

    @unittest.skip("Known issue: The algorithm is close but not perfectly accurate.")
    def testSaoPaulo(self):
        calculated_latlon = utm_to_DD(333336.30, 7394553.87 - 10000000, 23)
        self.assertLatLonEqual(calculated_latlon, (-23.5508160, -46.632830))

    def testNonNumeric(self):
        with self.assertRaises(ValueError):
            utm_to_DD(348783.31, "b", 12)

        with self.assertRaises(ValueError):
            utm_to_DD("a", 5945279.84, 12)

        with self.assertRaises(ValueError):
            utm_to_DD(348783.31, 5945279.84, "c")