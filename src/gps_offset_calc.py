"""
Calculates the GPS offsets from the centre of the image.
"""

def centre_gps_offset(pitch, roll, yaw, altitude):
    """
    yaw - heading angle of the plane (phi)
    pitch - pitch angle of the plane (theta). The positive direction is downward.
    roll - roll angle of the plane (psi). The positive direction is to the left.
    Airplane orientation angles are specified in radians.
    
    altitude - altitude value of the plane. Specified in meters.
    
    Returns:
    long_offset - longitudinal offset of the plane in DD.
    lat_offset - latitudinal offset of the plane in DD.
    """
    import math    
     
    if yaw == 0:
        long_offset = altitude * math.tan(roll)
        latitude_offset = altitude * math.tan(pitch) 
        
    else:
        long_offset = (math.cos(yaw) * altitude) * (math.tan(roll) + math.tan(pitch)) 
        lat_offset = (math.sin(yaw) * altitude) * (math.tan(roll) + math.tan(pitch)) 
        
    return (long_offset, lat_offset)


def offset_gps(long, lat, pitch, roll, yaw, altitude):
    """
    Calculates the GPS position of the centre of the image based on offsets. 
    """
    
    (long_offset, lat_offset) = centre_gps_offset(pitch, roll, yaw, altitude)
    long += long_offset
    lat += lat_offset
    return (long, lat) 
    
    