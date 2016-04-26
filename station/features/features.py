import os
import json
import pdb

from geo import Position

class Feature():
    """
    Base class for all features: features are things of interest
    in an image. Might be a point, an area, etc...

    name - some unique string that names or identifies the feature.
    """
    icon_name = "marker" # The UI will lookup an appropriate
                         # icon using this name.
    icon_size = (20, 20) # Width and height in pixels to draw the icon

    def __init__(self, name=""):
        self.picture = None # To be set later by the UI. This picture
                            # is intended to be a crop of the original
                            # image right around the feature.
        self.data = [("Name", name), ("Colour", ""), ("Letter", ""), ("Notes", ""), ("Export", True),]

    def __str__(self):
        if self.data:
            for name, value in self.data:
                if name == "Name":
                    if value:
                        return value
        return "(unnamed)"

    def dispLatLon(self):
        if self.position:
            return self.position.dispLatLon()
        else:
            return "(not on earth)"

class Point(Feature):
    def __init__(self, position, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.position = position


class GroundControlPoint(Point):
    icon_name = "x"
    icon_size = (10, 10)

class Marker(Point):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    icon_name = "flag"

    #positions = [self.position] #Im lost why this doesent work lol, will be edited when we do meta-markers

    def addPosition(self, newPosition): 
        positions.append(newPosition)
        _correctPosition()

    def _correctPosition(self):
        lat, lon = zip(*[position.latLon() for position in positions])
        cenLat = float(sum(lat))/float(len(lat)) # Finds the average latitude
        cenLon = float(sum(lon))/float(len(lon)) # Finds the average longitude
        position = [cenLat,cenLon] # Returns new as a tuple

def load_ground_control_points():
    """
    Returns a list of ground control points (GCP) as defined in the
    ground_control_points.json file.
    """
    location = os.path.join(*["data", "ground_control_points.json"])
    with open(location) as f:
        data = json.load(f)
    ground_control_points = []
    for id, value in data.items():
        position = Position(value[0], value[1])
        ground_control_points.append(GroundControlPoint(position, name=id))
    return ground_control_points

def load_ground_control_points_Dictionary():
        location = os.path.join(*["data", "ground_control_points.json"])
        with open(location) as f:
            data = json.load(f)
        return data