import os
import json
import pdb

from geo import Position, vector_between_positions
from collections import OrderedDict

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
        self.data = OrderedDict([("Name", name), ("Colour", ""), ("Letter", ""), ("Notes", ""), ("Export", True)])

    def __str__(self):
        if self.data:
            if self.data["Name"]:
                return self.data["Name"]
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
        self.data["GCP"] = ""
    icon_name = "flag"

class MetaMarker(Marker):
    """
    Describes a single real-world feature of interest appearing in an image.
    A MetaMarker is composed of a list of markers that have been used to mark
    that real-world feature.

    A MetaMarker can also be associated with a reference position; this is the
    "true" position of the real-word feature that the MetaMarker is associated with.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.positions = {}
        self.averagePosition = None
    icon_name = "flag"

    def addMarker(self, marker):
        self.positions[marker.data["Name"]] = marker.position
        self._correctPosition()

    def setReferencePosition(self, position):
        self.position = position

    def _correctPosition(self):
        """
        Sets the position of the MetaMarker using the positions of the
        component Markers.
        """
        lat, lon = zip(*[self.positions[name].latLon() for name in self.positions])
        cenLat = float(sum(lat))/float(len(lat)) # Finds the average latitude
        cenLon = float(sum(lon))/float(len(lon)) # Finds the average longitude
        self.averagePosition = Position(cenLat, cenLon)

    def _calcPositionError(self):
        """
        Calculates the error of each position in the Metamarker
        away from the reference position.
        """
        position_errors = {}
        for name in self.positions:
            position_errors[name] = vector_between_positions(self.positions[name], self.position)
        return position_errors

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
        ground_control_points = {}
        for id, value in data.items():
            position = Position(value[0], value[1])
            ground_control_points[id] = (GroundControlPoint(position, name=id))
        return ground_control_points
