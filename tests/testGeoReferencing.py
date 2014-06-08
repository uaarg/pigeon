import unittest

from GPSCoord import utm_to_DD, Position, Orientation, CameraSpecs, GeoReference

class BaseTestCase(unittest.TestCase):
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

    def assertPositionsEqual(self, position1, position2, check_height=False):
        """
        Asserts that the two provided positions are equal to within
        around 1/2 of a meter. Ignores altitude. Ignores height unless 
        check_height is specified as True.
        """
        self.assertLatLonEqual(position1.latLon(), position2.latLon())
        if check_height:
            self.assertAlmostEqual(position1.height, position2.height, places=1)

class UTMToDDTests(BaseTestCase):
    """
    Tests conversion of UTM to latitude longitude in decimal degrees (DD)

    Correct answers obtained using:
    http://www.latlong.net/lat-long-utm.html
    """

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
        calculated_latlon = utm_to_DD(335918.34, 6253113.37 - 10000000, 56)
        self.assertLatLonEqual(calculated_latlon, (-33.849525, 151.226451))

    def testCapeTown(self):
        calculated_latlon = utm_to_DD(262609.03, 6244778.96 - 10000000, 34)
        self.assertLatLonEqual(calculated_latlon, (-33.910679, 18.432394))

    def testParis(self):
        calculated_latlon = utm_to_DD(452170.72, 5411703.17, 31)
        self.assertLatLonEqual(calculated_latlon, (48.856450, 2.347951))

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

    def testInvalidUTMCoord(self):
        with self.assertRaises(Exception):
            utm_to_DD(900000, 5411703.17, 22) # easting out of range

        with self.assertRaises(Exception):
            utm_to_DD(333336.30, -10000000, 23) # northing out of range

    def testInvalidUTMZone(self):
        with self.assertRaises(Exception):
            utm_to_DD(378449.42, 4224578.88, 61)


class GeoReferencingTests(BaseTestCase):
    """
    Tests geo-referencing algorithms: determining the latitude and
    longitude of features on the earth in an image that was taken 
    from a plane.

    Distance from point calculations for correct positions done using:
    http://williams.best.vwh.net/gccalc.htm
    """
    def setUp(self):
        self.simple_camera = CameraSpecs(1000, 500, 30, 15)
        self.image_center_x = self.simple_camera.image_width/2
        self.image_center_y = self.simple_camera.image_height/2

        self.geo_reference = GeoReference(self.simple_camera)


        self.plane_position = Position(53.634426, -113.287097, 100)
        self.orientation = Orientation(0, 0, 0)

    def assertGeoReferencing(self):
        """
        """
        feature_position = self.geo_reference.pointInImage(self.plane_position,
                self.orientation, self.image_center_x, self.image_center_y)

        self.assertPositionsEqual(feature_position, self.correct_position)

    def testPerfectlyLevel(self):
        self.correct_position = self.plane_position
        self.assertGeoReferencing()

    def testSimple45Roll(self):
        self.orientation = Orientation(0, 45, 0)
        self.correct_position = Position(53.634427, -113.288608)
        self.assertGeoReferencing()

    def testNegative45Roll(self):
        self.orientation = Orientation(0, -45, 0)
        self.correct_position = Position(53.634427, -113.285585)
        self.assertGeoReferencing()

    def test45Roll234Yaw(self):
        self.orientation = Orientation(0, -45, 234)
        self.correct_position = Position(53.635153, -113.287985)
        self.assertGeoReferencing()

    def testSimple45Pitch(self):
        self.orientation = Orientation(45, 0, 0)
        self.correct_position = Position(53.635325, -113.287097)
        self.assertGeoReferencing()

    def test45Pitch90Yaw(self):
        self.orientation = Orientation(45, 0, 90)
        self.correct_position = Position(53.634427, -113.285585)
        self.assertGeoReferencing()



