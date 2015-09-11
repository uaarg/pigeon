import os
import json

from geo import Position

class Feature:
    """
    Base class for all features: features are things of interest
    in an image. Might be a point, an area, etc...
    """
    icon_name = "marker" # The UI will lookup an appropriate
                         # icon using this name.
    icon_size = (20, 20) # Width and height in pixels to draw the icon

    def __init__(self):
        self.picture = None # To be set later by the UI. This picture
                            # is intended to be a crop of the original
                            # image right around the feature.
        self.data = [("Name", ""), ("Colour", ""), ("Letter", ""), ("Notes", ""), ("Export", True)]

    def __str__(self):
        if self.data:
            for name, value in self.data:
                if name == "Name":
                    if value:
                        return value
        return "(unnamed)"

class Point(Feature):
    def __init__(self, position):
        super().__init__()
        self.position = position


class GroundControlPoint(Point):
    icon_name = "x"
    icon_size = (10, 10)

class Marker(Point):
    icon_name = "flag"


def load_ground_control_points():
    """
    Returns a list of ground control points (GCP) as defined in the 
    ground_control_points.json file.
    """
    location = os.path.join(*["data", "ground_control_points.json"])
    with open(location) as f:
        data = json.load(f)
    ground_control_points = []
    for key, value in data.items():
        position = Position(value[0], value[1])
        ground_control_points.append(GroundControlPoint(position))
    return ground_control_points