import os
import json

from geo import Position

class Point:
    def __init__(self, name, position):
        self.name = name
        self.position = position

class GroundControlPoint(Point):
    pass

class Marker(Point):
    pass


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
        ground_control_points.append(GroundControlPoint(key, position))
    return ground_control_points