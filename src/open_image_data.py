"""
Opens text files produced by the onboard imaging software, converts the given UTM coordinates to Decimal Degree / DMS coordinates.
"""

from utm_dd_convert import utm_to_DD

def get_image_data(image_ids, info_dir):
    """
    image_ids - A list of the ids of the images to be processed.
    info_dir - The directory that the image information is located in.
    """
    
    # Names of data fields in image information files
    ROLL_FIELD = "psi"
    PITCH_FIELD = "theta" 
    YAW_FIELD = "phi"
    ALTITUDE_FIELD = "alt"
    SPEED_FIELD = "speed"
    UTM_EAST_FIELD = "utm_east"
    UTM_NORTH_FIELD = "utm_north"
    
    # UTM zone info
    UTM_ZONE = 19
   
    # Data structures for storage of image data 
    orientation = {}
    position = {}
    coordinates = {}
    
    for i_id in image_ids: # A loop that goes through the id of every image we want to process
       info_file_location = ("%s/%s.txt" %(info_dir, i_id))
       print("\n== Image ID: %s ==" %i_id)

       # Get plane orientation information
       pitch = get_info_field(info_file_location, PITCH_FIELD) # get_info_field is actually another function that I wrote the code for, you can find its code later in this file.
       roll = get_info_field(info_file_location, ROLL_FIELD)
       yaw = get_info_field(info_file_location, YAW_FIELD)
       orientation[i_id] = {"pitch":pitch, "roll":roll, "yaw":yaw}
      
       # Get plane position information      
       altitude = get_info_field(info_file_location, ALTITUDE_FIELD)
       speed = get_info_field(info_file_location, SPEED_FIELD)
       position[i_id] = {"altitude":altitude, "speed":speed}

       # Get UTM coordinates
       UTM_easting = get_info_field(info_file_location, UTM_EAST_FIELD)
       UTM_northing = get_info_field(info_file_location, UTM_NORTH_FIELD)
       coordinates[i_id] = utm_to_DD(UTM_easting, UTM_northing, UTM_ZONE)
    
    return orientation, position, coordinates
       
def get_info_field(info_file_loc, field_name):
   """
   Gets the information in a field of the image info file specified by field_name.
   
   info_file_name - name of the image info file. 
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