"""
Main code for operation of ground station.
"""

def main():
    """
    Usage:
    ground_station <info_directory>
    
    info_directory - directory where the data associated with the images are contained.
    """
    
    import sys 
    from open_image_data import get_image_data, get_info_field 
    from utm_dd_convert import utm_to_DD
    from gps_offset_calc import offset_gps
 
    orientation = {}
    position = {}
    coordinates = {}
  
    try:
        info_directory = sys.argv[1]
    except:
        print("Usage: <info_directory>")
        sys.exit(-1)
        
    # TODO: Better input handling
   
    image_ids = input("Enter the IDs of the images of interest, separated by commas:\n")
    image_ids = image_ids.strip(' ')
    image_ids = image_ids.split(',')
    (orientation, position, coordinates) = get_image_data(image_ids, info_directory)
    print(orientation)
    print(position)
    print(coordinates)

   
    for i_id in image_ids:
        print("\n== Image ID: %s ==" %i_id)
        
        latitude = coordinates[i_id][0]
        longitude = coordinates[i_id][1]
        print("Latitude:", latitude)
        print("Longitude:", longitude)
        
        altitude = position[i_id]["altitude"]
        speed = position[i_id]["speed"]
        
        pitch = orientation[i_id]["pitch"]
        roll = orientation[i_id]["roll"]
        yaw = orientation[i_id]["yaw"]
        print("Pitch:", pitch)
        print("Roll:", roll)
        print("Yaw:", yaw)
       
        """
        (offset_latitude, offset_longitude) = offset_gps(longitude, latitude, pitch, roll, yaw, altitude)
        print("Offset latitude: ", offset_latitude)
        print("Offset longitude: ", offset_longitude)
        """
if __name__ == "__main__":
    main()