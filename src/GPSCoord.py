
"""
Functions for basic GPS coordinate processing.
Covers:
    - Extracting info from a text file sent with the images.
    - Converting UTM coordinates sent by the GPS to Decimal Degree coords.
    - Georeferencing features in an image.
    - Calculating properties of a series of points (ex. length, area)

Cindy Xiao <dixin@ualberta.ca>
Cameron Lee <cwlee1@ualberta.ca>
Emmanuel Odeke <odeke@ualberta.ca>
"""

import os
import re
import sys
import collections
import pyproj
from shapely.geometry import shape, Polygon
from math import *
from statistics import mean

ATTR_VALUE_REGEX_COMPILE = re.compile('([^\s]+)\s*=\s*([^\s]+)\s*', re.UNICODE)
__INFO_FILE_CACHE__ = collections.defaultdict(lambda: None)


class Position:
    """
    Position in 3D space of an object relative to the earth.
    Latitude and longitude are for the WGS84 datum.
    """
    def __init__(self, lat, lon, height=0, alt=None):
        """
        lat - latitude in degrees
        lon - longitude in degrees
        height - height above ground in meters
        alt - altitude above sea level in meters
        """
        self.lat = lat
        self.lon = lon
        self.height = height
        self.alt = alt

    def __str__(self):
        output = "(%s, %s)" % (self.lat, self.lon)

        if self.height != 0:
            output += " height=%s" % self.height

        if self.alt is not None:
            output += " alt=%s" % self.alt

        return output

    def __eq__(self, other):
        return self.lat == other.lat and self.lon == other.lon and self.height == other.height and self.alt == other.alt

    def latLon(self):
        return (self.lat, self.lon)


class Orientation:
    """
    Orientation of an object with respect to the earth.
    """
    def __init__(self, pitch, roll, yaw):
        """
        pitch - angle of the nose above the horizontal plane (theta)
                in degrees
        roll - angle of the left wing above the horizontal plane (phi)
                in degrees
        yaw - angle of the nose from true north along the horizontal (psi)
                plane measured clockwise in degrees
        """
        self.pitch = pitch
        self.roll = roll
        self.yaw = yaw

        self.pitch_rad = radians(pitch)
        self.roll_rad = radians(roll)
        self.yaw_rad = radians(yaw)

class CameraSpecs:
    """
    Camera constants needed for geo-referencing.
    """
    def __init__(self, image_width, image_height, field_of_view_horiz, field_of_view_vert):
        """
        image_width - the horizontal size of the image in pixels.
        image_height - the vertical size of the image in pixels.
        field_of_view_horiz - the angle between the camera and 
                the left and right edges of the image. In degrees.
        field_of_view_vert - the angle between the camera and
                the top and bottom edges of the image. In degrees.
        """
        self.image_width = image_width
        self.image_height = image_height

        self.field_of_view_horiz = field_of_view_horiz
        self.field_of_view_vert = field_of_view_vert

        self.field_of_view_horiz_rad = radians(self.field_of_view_horiz)
        self.field_of_view_vert_rad = radians(self.field_of_view_vert)

        # Used repeatedly in calculations so pre-calculating result for speed
        self.tan_angle_div_2_horiz = tan(self.field_of_view_horiz_rad/2)
        self.tan_angle_div_2_vert = tan(self.field_of_view_vert_rad/2)



class GeoReference:
    """
    Class for geo-referencing. Create an instance with the relatively
    contstant variables of the system. Then use the methods to perform 
    the desired type of geo-referencing.
    """
    def __init__(self, camera_specs):
        """
        Create an instance according to the specified system constants.
        """
        self.camera = camera_specs

    def centerOfImage(self, location, orientation):
        """
        Calculates and returns the position of the centre of the image.
        The plane location and orientation at the time 
        the image was taken should be provided 
        as Location and Orientation objects.
        """
        return self.pointInImage(location, orientation, self.camera.image_width/2, self.camera.image_height/2)

    def pointInImage(self, location, orientation, pixel_x, pixel_y):
        """
        Calculates and returns the position of the point located at 
        pixel_x, pixel_y in the image. The plane location and 
        orientation at the time the image was taken should be provided 
        as Location and Orientation objects.

        location - plane location
        orientation - plane orientation
        pixel_x - pixel in the image at the point. Measured from left 
                edge. Should be the same dimension as the image_width.
        pixel_y - pixel in the image at the point. Measured from bottom 
                edge. Should be the same dimension as the image_height.

        Algorithm described here: 
        sftp://uaargarchive@142.244.63.77/Upload/Ground Station Imaging/Geo-referencing Calculations
        https://drive.google.com/a/ualberta.ca/folderview?id=0BxmxpOgS5RpSbU1pWHN5dlBTelk&usp=sharing
        """

        camera = self.camera

        # Step 1: claculating angle offsets of pixel selected
        delta_theta_horiz = atan((2*pixel_x/camera.image_width - 1) * camera.tan_angle_div_2_horiz)
        delta_theta_vert = atan((2*pixel_y/camera.image_height - 1) * camera.tan_angle_div_2_vert)

        # Step 2: calculating effective pitch and roll
        pitch = orientation.pitch_rad + delta_theta_vert
        roll = orientation.roll_rad + delta_theta_horiz

        # Step 3: calculating level distance and angle to pixel
        distance_x = location.height * tan(pitch)
        distance_y = location.height * tan(-roll)
        distance = sqrt(pow(distance_x, 2) + pow(distance_y, 2))
        phi = atan2(distance_y, distance_x) # atan2 used to provide 
                # angle properly for any quadrant

        # Step 4: calculating angle from north to pixel
        forward_azimuth = phi + orientation.yaw_rad

        # Step 5: claculating endpoint using pyproj GIS module
        geod = pyproj.Geod(ellps="WGS84")
        pixel_lon, pixel_lat, back_azimuth = geod.fwd(location.lon, location.lat, degrees(forward_azimuth), distance)

        # print("pointInImage - distance: %.1f, bearing: %.1f, result: %.6f, %.6f" % (distance, degrees(forward_azimuth), pixel_lat, pixel_lon))

        return Position(pixel_lat, pixel_lon)


class PositionCollection:
    def __init__(self, positions, interior_positions_list=None):
        """
        Class for calculating properties of an ordered series of positions.

        A list of interior positions can be provided to define 
        holes in the polygon for area calculations or to be included in
        the perimeter for perimeter calculations. Note that this is a 
        list of lists of positions unlike the positions argument which 
        is just a list of positions.
        """
        self.positions = positions
        self.interior_positions_list = interior_positions_list

    def area(self):
        """
        Calculates the area of polygon defined by the sequence of 
        positions (and optional holes defined by interior_positions_list).
        """
        if len(self.positions) < 4:
            return 0

        lat, lon = zip(*[position.latLon() for position in self.positions])

        projection = pyproj.Proj(proj="aea", lat_1=min(lat), lat_2=max(lat), lat_0=mean(lat), lon_0=mean(lon))
            # Defining an equal area projection around the location of interest. aea stands for Albers equal-area

        def positions_to_coords(positions):
            lat, lon = zip(*[position.latLon() for position in positions])
                # Converting to a list of latitudes and a list of longitudes since this is what pyproj expects
            x, y = projection(lon, lat) # Projection the lat/lon into x/y
            coords = list(zip(x, y))
            return coords

        # Converting the outside of the polygon:
        coords = positions_to_coords(self.positions)

        # Now doing the same for the interiors, if any:
        if self.interior_positions_list:
            interior_coords_list = []
            for interior_positions in self.interior_positions_list:
                interior_coords_list.append(positions_to_coords(interior_positions))
        else:
            interior_coords_list = None

        # Creating the planar shape and getting its area
        polygon = Polygon(coords, interior_coords_list)
        if not polygon.is_valid:
            raise(ValueError("Positions do not define a valid polygon."))
        return polygon.area

    def _segment_length(self, positions, include_height, include_alt):
        """
        For internal use to keep things DRY.

        If include_height or include_alt is specified, factors is the
        vertical change between positions as part of the length.
        """
        if include_height and include_alt:
            raise(ValueError("Both include_height and include_alt specified. Must pick only one or neither."))

        length = 0
        geod = pyproj.Geod(ellps="WGS84")
        for i, position in enumerate(positions):
            if i == 0:
                continue
            position1 = positions[i-1]
            position2 = positions[i]
            lat1, lon1 = position1.latLon()
            lat2, lon2 = position2.latLon()
            forward_azimuth, back_azimuth, distance = geod.inv(lon1, lat1, lon2, lat2)

            if include_height:
                try:
                    delta_height = abs(position1.height - position2.height)
                except TypeError:
                    raise(ValueError("Valid height values must be provided for all positions when specifying include_height."))
                distance = sqrt(distance*distance + delta_height*delta_height)

            if include_alt:
                try:
                    delta_alt = abs(position1.alt - position2.alt)
                except TypeError:
                    raise(ValueError("Valid alt values must be provided for all positions when specifying include_alt."))

                distance = sqrt(distance*distance + delta_alt*delta_alt)

            length += distance
        return length

    def perimeter(self, include_height=False, include_alt=False):
        """
        Returns the length around the outside of the polygon plus the 
        length around each hole (if interior_positions provided).
        Connects the last point to the first point if not already
        explicitely done.

        Specify include_height or include_alt to include height
        or altitude changes in the distance calculations (otherwise
        treats all positions as if on the surface of the earth).
        """
        if self.positions[0] != self.positions[-1]:
            positions = self.positions + [self.positions[0]]
        else:
            positions = self.positions

        length = 0

        if self.interior_positions_list:
            segments = [positions] + self.interior_positions_list
        else:
            segments = [positions]

        for segment in segments:
            length += self._segment_length(segment, include_height=include_height, include_alt=include_alt)
        return length

    def length(self, include_height=False, include_alt=False):
        """
        Returns the length along the provided points. Does not connect
        the last to the first automatically.

        Specify include_height or include_alt to include height
        or altitude changes in the distance calculations (otherwise
        treats all positions as if on the surface of the earth).
        """
        return self._segment_length(self.positions, include_height=include_height, include_alt=include_alt)


def getInfoDict(info_file_loc, needsRefresh=False):
    cachedInfoDict = __INFO_FILE_CACHE__.get(info_file_loc, None)
    if needsRefresh or cachedInfoDict is None: 
        if os.path.exists(info_file_loc):
            with open(info_file_loc, 'r') as f:
                dataIn=f.readlines()
                outDict = collections.defaultdict(lambda: 0.0)
                for line in dataIn:
                    line = line.strip('\n')
                    regexMatch = ATTR_VALUE_REGEX_COMPILE.match(line)
                    if regexMatch:
                        attr, value = regexMatch.groups(1)
                        
                        outDict[attr] = value
                
                __INFO_FILE_CACHE__[info_file_loc] = outDict
                return outDict

    return cachedInfoDict or collections.defaultdict(lambda: 0.0)


def getInfoField(info_file_loc, field_name):
    """
    Gets the information in a field of the image info file specified by field_name.
    Returns the data as a float.
    
    info_file_loc - name of the image info file. 
    field_name - name of the field whose information is being retrieved.
    """
    fileExtractedDict = getInfoDict(info_file_loc)
    if fileExtractedDict and hasattr(fileExtractedDict, 'get'):
        return fileExtractedDict.get(field_name, -1)
    else:
        return -1

def centre_gps_offset(pitch, roll, yaw, alt):
    """
    yaw - heading angle of the plane (psi, +psi = yaw right)
    pitch - pitch angle of the plane (theta, +theta = pitch up)
    roll - roll angle of the plane (phi, +phi = roll right) 
    Airplane orientation angles are specified in radians.
    Right and left are from the perspective of a pilot inside the plane.
    
    alt - altitude value of the plane. Specified in meters.
    dd_m_conv - conversion factor from decimal degrees to meters.
    
    Returns:
    x_off - horizontal offset of the plane in meters.
    y_off - latitudinal offset of the plane in meters.
    """
    import math

    x_off = 0
    y_off = 0
     
    if yaw == 0:
        # horizontal offset (x-dir) due to roll (psi)
        if math.tan(roll) < 0: # roll left - may need to change depending on how angles are handled
            x_off = alt * math.tan(roll) # +x offset
        else: # roll right
            x_off = -1 * alt * math.tan(roll) # -x offset

        # vertical offset (y-dir) due to pitch (theta)
        if math.tan(pitch) < 0: # pitch down - may need to change depending on how angles are handled 
            y_off = -1 * alt * math.tan(pitch) # -y offset
        else: # pitch up
            y_off = alt * math.tan(pitch) # +y offset
        
    else:
        x_off = (math.cos(yaw) * altitude) * (math.tan(roll) + math.tan(pitch)) 
        y_off = (math.sin(yaw) * altitude) * (math.tan(roll) + math.tan(pitch)) 
        
    return (x_off, y_off)


def offset_gps(lon, lat, pitch, roll, yaw, altitude):
    """
    Calculates the GPS position of the centre of the image based on offsets.
    Adds these offsets to the position of the centre of the image.
    Use different offset functions with this as desired.
    """
    
    (lon_offset, lat_offset) = centre_gps_offset(pitch, roll, yaw, altitude)
    lon += lon_offset
    lat += lat_offset

    return (lon, lat) 
    
    
def utm_to_DD(easting, northing, zone, hemisphere="northern"):
    """
    Converts a set of UTM GPS coordinates to WGS84 Decimal Degree GPS coordinates.
    Returns (latitude, longitude) as a tuple.
    easting - UTM easting in metres
    northing - UTM northing in metres
    zone - current UTM zone

    Note that no hemisphere is specified; in the southern hemisphere, this function expects the false northing (10 000 000m) to be subtracted.

    An exception will be raised if the conversion involves invalid values.
    """

    easting, northing, zone = float(easting), float(northing), int(zone)
    # Easting and Northing ranges from https://www.e-education.psu.edu/natureofgeoinfo/c2_p23.html
    if not (167000 < easting < 833000):
        raise(ValueError("Easting value is out of bounds."))
    if not (-9900000 < northing < 9400000):
        raise(ValueError("Northing value is out of bounds."))

    if not (1 <= zone <= 60):
        raise(ValueError("Zone value of %s is out of bounds" % zone))

    pr = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84', errcheck=True)

    lon, lat = pr(easting, northing, inverse=True)
    return lat, lon

