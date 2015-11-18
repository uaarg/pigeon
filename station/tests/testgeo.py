import unittest
import itertools

from geo import utm_to_DD, Position, Orientation, CameraSpecs, GeoReference, PositionCollection

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
        if position1 is None or position2 is None:
            self.assertEqual(position1, position2) # If both positions are None that counts as equal
        else:
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
        with self.assertRaises(ValueError):
            utm_to_DD(900000, 5411703.17, 22) # easting out of range

        with self.assertRaises(ValueError):
            utm_to_DD(333336.30, -10000000, 23) # northing out of range

    def testInvalidUTMZone(self):
        with self.assertRaises(ValueError):
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
        self.correct_position = Position(53.634426, -113.288608)
        self.assertGeoReferencing()

    def testNegative45Roll(self):
        self.orientation = Orientation(0, -45, 0)
        self.correct_position = Position(53.634426, -113.285585)
        self.assertGeoReferencing()

    def test45Roll234Yaw(self):
        self.orientation = Orientation(0, -45, 234)
        self.correct_position = Position(53.635153, -113.287985)
        self.assertGeoReferencing()

    def testSimple45Pitch(self):
        self.orientation = Orientation(45, 0, 0)
        self.correct_position = Position(53.635325, -113.287097)
        self.assertGeoReferencing()

    def testSimple30Pitch(self):
        self.orientation = Orientation(30, 0, 0)
        self.correct_position = Position(53.634945, -113.287097)
        self.assertGeoReferencing()

    def test45Pitch90Yaw(self):
        self.orientation = Orientation(45, 0, 90)
        self.correct_position = Position(53.634426, -113.285585)
        self.assertGeoReferencing()

    def testOutOfBoundYaw(self):
        """
        Tests out of range yaw values (below 0, above 360, etc...).
        Yaw value should be automatically adjusted to within range.
        """
        for offset in [-2, -1, 0, 1, 2]:
            yaw = 234 + 360 * offset
            self.orientation = Orientation(0, -45, yaw)
            self.correct_position = Position(53.635153, -113.287985)
            self.assertGeoReferencing()

    def testOutOfBoundRoll(self):
        """
        Tests out of range roll values (below -180, above 180, etc...).
        Roll value should be automatically adjusted to within range.
        """
        for offset in [-2, -1, 0, 1, 2]:
            roll = -45 + 360 * offset
            self.orientation = Orientation(0, roll, 234)
            self.correct_position = Position(53.635153, -113.287985)
            self.assertGeoReferencing()


    def testPointInSky(self):
        """
        Tests if the roll or pitch value is above 90 degrees. This
        would mean the point to be geo-referenced is in the sky. So
        should be None.
        """
        self.orientation = Orientation(0, 91, 0)
        self.correct_position = None
        self.assertGeoReferencing()

        self.orientation = Orientation(-91, 0, 0)
        self.correct_position = None
        self.assertGeoReferencing()


class GeoReferencingCameraSpecsTests(BaseTestCase):
    """
    Tests geo-referencing algorithms: determining the latitude and
    longitude of features on the earth in an image that was taken
    from a plane.

    Distance from point calculations for correct positions done using:
    http://williams.best.vwh.net/gccalc.htm
    """
    def setUp(self):
        self.plane_position = Position(53.634426, -113.287097, 100)
        self.orientation = Orientation(0, 0, 0)

    def assertGeoReferencing(self):
        """
        """
        self.geo_reference = GeoReference(self.camera)
        feature_position = self.geo_reference.pointInImage(self.plane_position,
                self.orientation, self.x, self.y)

        self.assertPositionsEqual(feature_position, self.correct_position)

    def testLevelTopOfImage30Up(self):
        self.camera = CameraSpecs(1000, 500, 30, 60)

        self.x = self.camera.image_width/2
        self.y = 0

        self.correct_position = Position(53.634945, -113.287097)

        self.assertGeoReferencing()

    def testLevelTopOfImage45Up(self):
        self.camera = CameraSpecs(1000, 500, 30, 90)

        self.x = self.camera.image_width/2
        self.y = 0

        self.correct_position = Position(53.635325, -113.287097)

        self.assertGeoReferencing()

    def testLevelTopOfImage60Up(self):
        self.camera = CameraSpecs(1000, 500, 30, 120)

        self.x = self.camera.image_width/2
        self.y = 0

        self.correct_position = Position(53.6359816, -113.287097)

        self.assertGeoReferencing()

    def testLevelLeftOfImage45Up(self):
        self.camera = CameraSpecs(1000, 500, 90, 30)

        self.x = 0
        self.y = self.camera.image_height/2

        self.correct_position = Position(53.634426, -113.288608)

        self.assertGeoReferencing()

class InverseGeoreferencingTests(BaseTestCase):
    """
    Tests the inverse geo-referencing algorithm (determining the pixel
    in the image of a location on the earth).
    """

    def assertAlmostEqual(self, *args, **kwargs):
        kwargs["places"] = 0 # Don't need sub-pixel accuracy
        super().assertAlmostEqual(*args, **kwargs)

    def testSimple45Roll(self):
        """
        Tests a simple, specific case.
        """
        camera = CameraSpecs(1000, 500, 30, 15)
        plane_position = Position(53.634426, -113.287097, 100)
        plane_orientation = Orientation(0, 45, 0)
        point_position = Position(53.634426, -113.288608)

        geo_reference = GeoReference(camera)

        pixel_x, pixel_y = geo_reference.pointOnImage(plane_position, plane_orientation, point_position)

        self.assertAlmostEqual(camera.image_width/2, pixel_x)
        self.assertAlmostEqual(camera.image_height/2, pixel_y)

    def testInverse(self):
        """
        Tests lots of input permutations by ensuring pointOnImage()
        is the inverse of pointInImage().
        """
        cameras = [CameraSpecs(1000, 500, 30, 15), CameraSpecs(400, 400, 50, 50)]
        plane_positions = [Position(53.634426, -113.287097, 100), Position(-33.849525, 151.226451, 200), Position(0, 0, 50)]
        plane_orientations = [Orientation(0, 45, 0), Orientation(10, 10, 0), Orientation(30, 40, 300)]

        for camera, plane_position, plane_orientation in itertools.product(cameras, plane_positions, plane_orientations):
            geo_reference = GeoReference(camera)
            for pixel_x, pixel_y in [(5, 10), (camera.image_width*0.1, camera.image_height*0.3), (camera.image_width/2, camera.image_height/2)]:
                point_position = geo_reference.pointInImage(plane_position, plane_orientation, pixel_x, pixel_y)
                calculated_pixel_x, calculated_pixel_y = geo_reference.pointOnImage(plane_position, plane_orientation, point_position)

                msg = "For camera=%s, plane_position=%s, plane_orientation=%s, pixel_x=%s, pixel_y=%s. point_position was %s" % (camera, plane_position, plane_orientation, pixel_x, pixel_y, point_position)
                self.assertNotEqual(calculated_pixel_x, None, msg=msg)
                self.assertNotEqual(calculated_pixel_y, None, msg=msg)
                self.assertAlmostEqual(pixel_x, calculated_pixel_x, msg=msg)
                self.assertAlmostEqual(pixel_y, calculated_pixel_y, msg=msg)


class AreaCalculationTests(BaseTestCase):
    """
    Correct answers from: http://www.earthpoint.us/Shapes.aspx
    """

    def assertAlmostEqual(self, *args, **kwargs):
        kwargs["places"] = 1
        super().assertAlmostEqual(*args, **kwargs)

    def testEmptyArea(self):
        """
        If the points provided define nothing, just a point, or just a line,
        then the area should be 0.
        """
        calculated_area = PositionCollection([]).area()
        self.assertEqual(calculated_area, 0)

        calculated_area = PositionCollection([Position(53, -113)]).area()
        self.assertEqual(calculated_area, 0)

        calculated_area = PositionCollection([Position(53, -113), Position(53.01, -113.001)]).area()
        self.assertEqual(calculated_area, 0)

    def testAreaSimple(self):
        locations = [Position(53.640376, -113.287968),
                     Position(53.639969, -113.285930),
                     Position(53.641470, -113.285865),
                     Position(53.641063, -113.287432)]
        calculated_area = PositionCollection(locations).area()
        self.assertAlmostEqual(calculated_area, 14515.74)

    def testAreaSmall(self):
        locations = [Position(53.63858895845907, -113.2858449974274),
                     Position(53.63871695800452, -113.2858515527736),
                     Position(53.63872128665391, -113.2860433590805),
                     Position(53.63858895868907, -113.2860271060327)]
        calculated_area = PositionCollection(locations).area()
        self.assertAlmostEqual(calculated_area, 178.96)

    def testAreaComplex(self):
        locations = [Position(38.14612244235001, -76.42605941380039),
                     Position(38.14557025842809, -76.4260394110355),
                     Position(38.1464050578743,  -76.42329134077552),
                     Position(38.1463024179381,  -76.42236638287116),
                     Position(38.14528885141904, -76.42215724758948),
                     Position(38.14422805636855, -76.42268283414849),
                     Position(38.14366797831114, -76.42184126223457),
                     Position(38.14396571089122, -76.41846735018396),
                     Position(38.15060936431924, -76.41864985065172),
                     Position(38.14998716757382, -76.4267023103049),
                     Position(38.14880902767541, -76.42648506976147),
                     Position(38.14876177614931, -76.42528994302296),
                     Position(38.14827224853664, -76.42506909773816),
                     Position(38.1477850368527,  -76.42497975447422),
                     Position(38.14758905846647, -76.42497564853529),
                     Position(38.14725924076873, -76.42496874021477),
                     Position(38.14701678016844, -76.42505456535311),
                     Position(38.14684321151271, -76.42547186145289),
                     Position(38.14712333083869, -76.42624364166178),
                     Position(38.14724720470556, -76.42694061104336),
                     Position(38.14664853608051, -76.42721561228375),
                     Position(38.14559495995302, -76.42723612427338),
                     Position(38.14464229313943, -76.42710553328192),
                     Position(38.14457479586402, -76.42640560039129),
                     Position(38.1455702150766,  -76.42658573372728),
                     Position(38.14624881836266, -76.42684902051074),
                     Position(38.1464912488537,  -76.42684131329734),
                     Position(38.14659388833043, -76.42632759464361),
                     Position(38.14612244235001, -76.42605941380039)]
        calculated_area = PositionCollection(locations).area()
        self.assertAlmostEqual(calculated_area, 399631.38)

    def testAreaSmall(self):
        locations = [Position(53.63858895845907, -113.2858449974274),
                     Position(53.63871695800452, -113.2858515527736),
                     Position(53.63872128665391, -113.2860433590805),
                     Position(53.63858895868907, -113.2860271060327)]
        calculated_area = PositionCollection(locations).area()
        self.assertAlmostEqual(calculated_area, 178.96)

    def testAreaCCW(self):
        locations = [
                     Position(53.63858895868907, -113.2860271060327),
                     Position(53.63872128665391, -113.2860433590805),
                     Position(53.63871695800452, -113.2858515527736),
                     Position(53.63858895845907, -113.2858449974274)]
        calculated_area = PositionCollection(locations).area()
        self.assertAlmostEqual(calculated_area, 178.96)

    def testAreaBowTie(self):
        locations = [Position(49.9075074454562, -98.27381389704948),
                     Position(49.90870140727183, -98.27199796319962),
                     Position(49.9090626965297, -98.27026881457152),
                     Position(49.90766478562761, -98.2710446237257),
                     Position(49.90937980170813, -98.27461239710256)]
        with self.assertRaises(ValueError):
            calculated_area = PositionCollection(locations).area()

    def testAreaGreenwhich(self):
        """
        Tests that areas which cross the prime meridian are handled correctly.
        """
        locations = [Position(51.48212172072677, -0.002771281514114237),
                     Position(51.48204262113154, 0.002880768718658212),
                     Position(51.48567704805823, 0.003183298765256712),
                     Position(51.48571103900387, -0.002685273093026672),
                     Position(51.48212172072677, -0.002771281514114237)]
        calculated_area = PositionCollection(locations).area()
        self.assertAlmostEqual(calculated_area, 160880.36)

    def testAreaEquator(self):
        """
        Tests that areas which cross the equator are handled correctly.
        """
        locations = [Position(0.0007322725219188839, -50.66495399830471),
                     Position(-0.00106961883117696, -50.66483373897671),
                     Position(-0.001109697280278675, -50.66303324085633),
                     Position(0.000704133213207757, -50.66303196301214),
                     Position(0.0007322725219188839, -50.66495399830471)]
        calculated_area = PositionCollection(locations).area()
        self.assertAlmostEqual(calculated_area, 41393.96)

    def testAntiMeridian(self):
        """
        Tests that areas which cross from longitude of -180 to 180.
        """
        locations = [Position(28.82476660691798, 179.9815165741115),
                     Position(28.81139628735658, 179.9843389900523),
                     Position(28.81111032916015, 179.9844042620045),
                     Position(28.81548096514992, -179.986990416172), # 180.013009583828
                     Position(28.83679214641581, -179.989474692512), # 180.0105253074883
                     Position(28.83633625913864, 179.9890348396868),
                     Position(28.82636640590886, 179.9908104088083),
                     Position(28.82476660691798, 179.9815165741115)]
        calculated_area = PositionCollection(locations).area()
        self.assertAlmostEqual(calculated_area, 6496608.18)


    def testSouthernHemisphere(self):
        locations = [Position(-33.85648753781738, 151.2167346164685),
                     Position(-33.85653688889253, 151.2170107526296),
                     Position(-33.85723388355765, 151.2168419382072),
                     Position(-33.85690927283394, 151.2174174065159),
                     Position(-33.85638296117077, 151.217273679916),
                     Position(-33.856280417931, 151.2166540661909),
                     Position(-33.8561565141336, 151.2165050031699),
                     Position(-33.85615167691103, 151.2164707363791),
                     Position(-33.85614677095479, 151.2162109302047),
                     Position(-33.8567845959764, 151.2160473417744),
                     Position(-33.85709009653129, 151.21614005947),
                     Position(-33.85648753781738, 151.2167346164685)]
        calculated_area = PositionCollection(locations).area()
        self.assertAlmostEqual(calculated_area, 7322.28)

    def testHolyArea(self):
        """
        Tests that excluding interior regions works.
        """
        locations = [Position(38.87253259892824, -77.05788457660967),
                     Position(38.87291016281703, -77.05465973756702),
                     Position(38.87053267794386, -77.05315536854791),
                     Position(38.868757801256,   -77.05552622493516),
                     Position(38.86996206506943, -77.05844056290393),
                     Position(38.87253259892824, -77.05788457660967)]

        inner_locations = [Position(38.87154239798456, -77.05668055019126),
                           Position(38.87167890344077, -77.05542625960818),
                           Position(38.87076535397792, -77.05485125901024),
                           Position(38.87008686581446, -77.05577677433152),
                           Position(38.87054446963351, -77.05691162017543),
                           Position(38.87154239798456, -77.05668055019126)]
        calculated_area = PositionCollection(locations, [inner_locations]).area()
        self.assertAlmostEqual(calculated_area, 120948.23)

class PerimeterCalculationTests(BaseTestCase):
    """
    Correct answers from: http://www.earthpoint.us/Shapes.aspx
    """

    def assertAlmostEqual(self, *args, **kwargs):
        kwargs["places"] = 1
        super().assertAlmostEqual(*args, **kwargs)

    def testSouthernHemisphere(self):
        locations = [Position(-33.85648753781738, 151.2167346164685),
                     Position(-33.85653688889253, 151.2170107526296),
                     Position(-33.85723388355765, 151.2168419382072),
                     Position(-33.85690927283394, 151.2174174065159),
                     Position(-33.85638296117077, 151.217273679916),
                     Position(-33.856280417931, 151.2166540661909),
                     Position(-33.8561565141336, 151.2165050031699),
                     Position(-33.85615167691103, 151.2164707363791),
                     Position(-33.85614677095479, 151.2162109302047),
                     Position(-33.8567845959764, 151.2160473417744),
                     Position(-33.85709009653129, 151.21614005947),
                     Position(-33.85648753781738, 151.2167346164685)]
        calculated_perimeter = PositionCollection(locations).perimeter()
        self.assertAlmostEqual(calculated_perimeter, 528.23)

    def testWithoutExplicitClose(self):
        """
        Tests that the perimeter is calculated correctly even if the last
        point isn't equal to the first point.
        """
        locations = [Position(-33.85648753781738, 151.2167346164685),
                     Position(-33.85653688889253, 151.2170107526296),
                     Position(-33.85723388355765, 151.2168419382072),
                     Position(-33.85690927283394, 151.2174174065159),
                     Position(-33.85638296117077, 151.217273679916),
                     Position(-33.856280417931, 151.2166540661909),
                     Position(-33.8561565141336, 151.2165050031699),
                     Position(-33.85615167691103, 151.2164707363791),
                     Position(-33.85614677095479, 151.2162109302047),
                     Position(-33.8567845959764, 151.2160473417744),
                     Position(-33.85709009653129, 151.21614005947)]
        calculated_perimeter = PositionCollection(locations).perimeter()
        self.assertAlmostEqual(calculated_perimeter, 528.23)

class LengthCalculationTests(BaseTestCase):
    """
    Correct answers mostly from: http://www.earthpoint.us/Shapes.aspx
    """

    def assertAlmostEqual(self, *args, **kwargs):
        kwargs["places"] = 1
        super().assertAlmostEqual(*args, **kwargs)

    def testSimple(self):
        """
        Tests that the perimeter is calculated correctly even if the last
        point isn't equal to the first point.
        """
        locations = [Position(53.634426, -113.287097),
                     Position(53.634427, -113.288608)]
        calculated_length = PositionCollection(locations).length()
        self.assertAlmostEqual(calculated_length, 100)

    def testHeightChange(self):
        locations = [Position(53.634426, -113.287097, 100),
                     Position(53.634427, -113.288608)]
        calculated_length = PositionCollection(locations).length(include_height=True)
        self.assertAlmostEqual(calculated_length, 141.42)

    def testAltitudeChange(self):
        locations = [Position(53.634426, -113.287097, alt=610),
                     Position(53.634427, -113.288608, alt=710)]
        calculated_length = PositionCollection(locations).length(include_alt=True)
        self.assertAlmostEqual(calculated_length, 141.42)

    def testMissingAlt(self):
        locations = [Position(53.634426, -113.287097, alt=610),
                     Position(53.634427, -113.288608)]
        with self.assertRaises(ValueError):
            calculated_length = PositionCollection(locations).length(include_alt=True)
