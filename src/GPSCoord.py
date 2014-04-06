
"""
Functions for basic GPS coordinate processing.
Covers:
    - Extracting info from a text file sent with the images.
    - Converting UTM coordinates sent by the GPS to Decimal Degree coords.

Cindy Xiao <dixin@ualberta.ca>
"""

def getInfoField(info_file_loc, field_name):
    """
    Gets the information in a field of the image info file specified by field_name.
    
    info_file_loc - name of the image info file. 
    field_name - name of the field whose information is being retrieved.
    """
    import re
    
    fin = open(info_file_loc, 'r') 
    
    # Search for field data
    field_regex = re.compile( r'%s\s*=\s*(-?\d+\.?\d+)\n?' % (field_name))
    data =  field_regex.findall( fin.read() )[0] # Better way to extract data from single-element list?
    try:
        float(data)
    except:
        data = 0
    print("Field %s: %s" %(field_name, data) )
    
    fin.close()
    
    return data

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
