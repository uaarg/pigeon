
"""
Functions for basic GPS coordinate processing.
Covers:
    - Extracting info from a text file sent with the images.
    - Converting UTM coordinates sent by the GPS to Decimal Degree coords.
    - Georeferencing features in an image.

Cindy Xiao <dixin@ualberta.ca>
Cameron Lee <cwlee1@ualberta.ca>
Emmanuel Odeke <odeke@ualberta.ca>
"""

import os
import re
import sys
import collections

ATTR_VALUE_REGEX_COMPILE = re.compile('([^\s]+)\s*=\s*([^\s]+)\s*', re.UNICODE)

try:
    import pyproj
except ImportError as e:
    sys.stderr.write(
        "\033[91mNeeds module 'pyproj'. Install it by 'pip install pyproj' or 'easy_install pyproj'\n\033[00m"
    )
    sys.exit(-1)
    
from math import *

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
        camera = self.camera

        # Step 2: calculating effective pitch and roll
        pitch = orientation.pitch_rad
        roll = orientation.roll_rad

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
        print('pixel_lat', pixel_lat, 'pixel_lon', pixel_lon)

        return Position(pixel_lat, pixel_lon)

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
        delta_theta_horiz = atan((2*pixel_x/camera.image_width - 1) / camera.tan_angle_div_2_horiz)
        delta_theta_vert = atan((2*pixel_y/camera.image_height - 1) / camera.tan_angle_div_2_vert)

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
    
    
def utm_to_DD(x, y, zone, mode = "DD"):
    """
    Converts a set of UTM GPS coordinates to Decimal Degree or DMS coodinates.
    Returns lat, long as a list with 2 items.
    x - UTM easting
    y - UTM northing
    zone - current UTM zone
    mode - conversion to Decimal Degrees (mode = DD) or DMS (mode = DMS)
    """
    
    import math
    
    # Check for validity of UTM coordinates
    # TODO: Check for correct range of coordinates
    try:
        x = float(x)
        y = float(y)
        zone = int(zone)
    except ValueError as e:
        raise(ValueError("The UTM coordinates given are invalid: %s" % (str(e),)))
    
    # (x, a, b, k0, e, e1sq, M, mu, e1, e1a, e2, j1, j2, j3, j4, fp, C1, T1, R1, R2, N1) = 0
    # (N2, D, Q1, Q2, Q3, Q4, Q5, Q6, Q7, lat, lon, lon0) = 0   
    x0 = 500000 - x;
    a = 6378137;
    b = 6356752.3142;
    k0 = 0.9996;
    e = 0.081819191; # double e = math.sqrt(1-math.pow(b, 2)/math.pow(b, 2));
    e1sq = 0.006739497;
    lon0 = -177 + 6*(zone-1); # zones
        
    # Calculate the Meridional Arc
    M = y/k0;
    
    # Calculate the footprint latitude
    mu = M/(a*(1 - (math.pow(e,2))/4 - 3*(math.pow(e,4))/64 - 5*(math.pow(e,6))/256));
    e1a = 1-(math.pow(e,2));
    e1 = (1-(math.pow(e1a, 0.5))) /(1+(math.pow(e1a, 0.5)));
    
    j1 = 3*e1/2-27*math.pow(e1,3)/32;
    # j2 = 21*math.pow(e1,2)/2-55*math.pow(e1,4)/32; # error /2 = /16
    j2 = 21*math.pow(e1,2)/15-55*math.pow(e1,4)/32;
    j3 = 151*math.pow(e1,3)/96;
    j4 = 1097*math.pow(e1,4)/512;
    
    fp = mu + j1*math.sin(2*mu) + j2*math.sin(4*mu) + j3*math.sin(6*mu) + j4*math.sin(8*mu);
    
    # Calculate Latitude and Longitude
    e2 = (math.pow(e,2))/e1a;
    C1 = e2*math.pow(math.cos(fp),2);
    T1 = math.pow(math.tan(fp),2);
    
    R2 = math.pow(e,2)*math.pow(math.sin(fp),2);
    R1 = a*e1a/math.pow(1-R2,1.5);
    
    N2 = math.pow(e,2)*math.pow(math.sin(fp),2);
    N1 = a/math.pow(1-N2,0.5);
    D = x0/(N1*k0);
     
    # Latitude
    Q1 = N1 * math.tan(fp)/R1;
    Q2 = math.pow(D,2)/2;
    Q3 = (5 + 3*T1 + 10*C1-4*math.pow(C1,2)-9*e2)*math.pow(D,4)/24;
    Q4 = (61 + 90*T1 + 298*C1+45*math.pow(T1,2)-3*math.pow(C1,2)-252*e2)*math.pow(D,6)/720;
    # lat = (180/Math.PI)*(fp - Q1*(Q2 - Q3 + Q4)); # angle is in radian jezz
    lat = math.degrees(fp - Q1*(Q2 - Q3 + Q4)); # angle is in radian jezz
    
    # Longitude 
    Q5 = D;
    Q6 = (1 + 2*T1 + C1) * math.pow(D,3)/6;
    Q7 = (5-2*C1+28*T1-3*math.pow(C1,2) + 8 * e1sq + 24 * math.pow(T1,2))*math.pow(D,5)/120;
    
    lon = lon0 - math.degrees((Q5 - Q6 + Q7)/math.cos(fp));
    
    return (lat, lon)
