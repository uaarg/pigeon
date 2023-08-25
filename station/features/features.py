import os
import json
import pickle
import base64
import uuid
import io

from station.geo import Position, PositionCollection, position_at_offset
from station.image import ImageCrop


class FeatureDeserializeSecurityError(Exception):
    pass


class WhiteListUnpickler(pickle.Unpickler):
    """
    Only allows unpickling of certain classes. Provides some security
    from remote code execution. For details see:
    https://docs.python.org/3.4/library/pickle.html#restricting-globals

    Add classes set as attributes of BaseFeature or any subclasses here.
    """
    allowed_classes = [
        ("image.image", "Image"),
        ("image.image", "ImageCrop"),
        ("geo.geo", "Orientation"),
        ("geo.geo", "Position"),
        ("geo.geo", "GeoReference"),
        ("geo.geo", "CameraSpecs"),
        ("ui.pixmaploader", "PixmapLoader"),
        ("PyQt5.QtGui", "QPixmap"),
        ("features.features", "BaseFeature"),
        ("features.features", "PointOfInterest"),
        ("features.features", "Marker"),
        ("features.features", "Feature"),
        ("features.features", "GroundControlPoint"),
    ]

    def find_class(self, module, name):
        if (module, name) in self.allowed_classes:
            return super().find_class(module, name)
        else:
            raise FeatureDeserializeSecurityError(
                "Not allowed to unpickle %s.%s because it hasn't been listed as safe. "
                % (module, name) +
                "Either it should be added to the whitelist or an intrusion was just prevented."
            )


def loads_whitelisted(string):
    return WhiteListUnpickler(io.BytesIO(string)).load()


class BaseFeature:
    """
    Base class for features and feature-like things.
    """
    picture_crop = None
    thumbnail = None
    data = []

    def __init__(self):
        self.id = str(
            uuid.uuid4()
        )[:
          8]  # Unique identifier for this feature accross all Pigeon instances

    def __str__(self):
        if self.data:
            for field in self.data:
                key = field[0]
                value = field[1]
                if key == "Name":
                    if value:
                        return str(value)
        return "(unnamed)"

    def subfeatures(self):
        return []

    def allowSubfeatures(self):
        return False

    def updateSubfeature(self, feature):
        """
        Updates the subfeature matching the provided feature (by id)
        and returns True. If not match is found, returns False instead.
        """
        return False

    def serialize(self):
        """
        Returns a string that can be used to re-create this object using deserialize().

        Subclasses should not need to re-implement. Uses pickle to automatically get
        everything.
        """
        # Ivybus expects a normal string but pickle gives a binary string. So b64 encoding.
        data = base64.b64encode(pickle.dumps(self)).decode("ascii")
        return data

    @classmethod
    def deserialize(cls, dumped):
        """
        Returns a new instance of this class from a string created using serialize().
        """
        return loads_whitelisted(base64.b64decode(dumped))


class PointOfInterest(BaseFeature):
    """
    Class for each point in an image that's interesting.

    Could the location of a Point Feature, corner of an Area Feature,
    etc... as seen in a particular image. AKA, an instance of feature
    or part of a feature.
    """

    def __init__(self, image, position, icon_name, icon_size, name=""):
        super().__init__()

        self.image = image
        self.position = position
        self.icon_name = icon_name
        self.icon_size = icon_size

        self.data = [("Name", name), ("Notes", "")]

        self._determinePointOnImage()

    def __repr__(self):
        return "%s(image=%r, position=%r)" % (self.__class__.__name__,
                                              self.image, self.position)

    def _determinePointOnImage(self):
        if self.image:
            self.point_on_image = self.image.invGeoReferencePoint(
                self.position)
        else:
            self.point_on_image = (None, None)

    def updatePosition(self, position):
        self.position = position
        self._determinePointOnImage()


class Feature(BaseFeature):
    """
    Base class for all features: features are things of interest
    on the ground. Might be a point, an area, etc...
    """

    def __init__(self, name=""):
        super().__init__()
        #self.data = [("Name", name), ("Colour", ""), ("Letter", ""), ("Notes", ""), ("Export", True)]
        self.data = [
            ("Name", name),
            ("Type", "", ["", "standard", "qrc", "off_axis", "emergent"]),
            ("Shape", "", [
                "", "circle", "semicircle", "quarter_circle", "triangle",
                "square", "rectangle", "trapezoid", "pentagon", "hexagon",
                "heptagon", "octagon", "star", "cross"
            ]),
            ("Orientation", "",
             ["", "N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
            ("Bkgnd_Color", "", [
                "", "white", "black", "gray", "red", "blue", "green", "yellow",
                "purple", "brown", "orange"
            ]), ("Alphanumeric", ""),
            ("Alpha_Color", "", [
                "", "white", "black", "gray", "red", "blue", "green", "yellow",
                "purple", "brown", "orange"
            ]), ("Notes", ""), ("Export", True)
        ]

        # Holds references from external programs to this feature.
        # An external program should register its own entry in this dictionary;
        # all resources related to that program should be registered
        # in that entry.
        self.external_refs = {}

    def data_as_dict(self):
        """
        Retruns the data variable as a dictionary for easier usage
        For example, key could be `Type` and a value could be `standard`

        Return:
            (dict)  Dictionary form of data
        """

        data_dict = {item[0]: item[1] for item in self.data}
        return data_dict


class Point(Feature):
    """
    Base class for features on the ground that are described by a
    single point.
    """

    def __init__(self, image, position=None, point=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not position and not point:
            raise TypeError("Must provide either a position or a point.")
        elif position and point:
            raise TypeError("Can't provided a position and a point.")
        elif point:
            position = image.geoReferencePoint(point[0], point[1])

        # The feature could be spotted in multiple images so keeping track of them all here.
        self.instances = {
            image:
            PointOfInterest(image,
                            position,
                            self.icon_name,
                            self.icon_size,
                            name="(in image %s)" % image)
        }

        self.viewed_instances = {
        }  # For instances shown to the user but not set by them yet.

    def updatePosition(self, image, position):
        """
        Set or update the position that this Point is visible at in the provided
        image.
        """
        if image in self.instances.keys():
            self.instances[image].updatePosition(position)
        else:
            self.instances[image] = PointOfInterest(image,
                                                    position,
                                                    self.icon_name,
                                                    self.icon_size,
                                                    name="(in image %s)" %
                                                    image)

    def updatePoint(self, image, point):
        """
        Set or update the position that this Point is visible at in the provided
        image, by the point in the image Point is visible at.
        """
        self.updatePosition(image, image.geoReferencePoint(point[0], point[1]))

    def updatePointById(self, id_, image, point):
        """
        Set or update the position that this Point is visible at in the provided
        image, if the provided id_ is for this Point. If it is, returns True.
        Otherwise, returns False.
        """
        if id_ in [instance.id for instance in self.instances.values()]:
            self.updatePoint(image, point)
            return True
        elif id_ in [
                instance.id for instance in self.viewed_instances.values()
        ]:
            for instance_image, instance in self.viewed_instances.items():
                if instance.id == id_:
                    self.instances[image] = self.viewed_instances[
                        instance_image]
                    self.updatePoint(image, point)
                    return True
        else:
            return False

    def _positionCollection(self):
        positions = []
        for image, instance in self.instances.items():
            positions.append(instance.position)
        if positions:
            return PositionCollection(positions)

    @property
    def position(self):
        return self._positionCollection().center()

    def visiblePoints(self, image):
        """
        Returns a list of PointOfInterest objects that are visible
        in the provided image. Can be used for showing them in the UI,
        etc...
        """
        if image in self.instances.keys():
            return [self.instances[image]]
        else:
            self.viewed_instances[image] = PointOfInterest(
                image,
                self.position,
                self.icon_name,
                self.icon_size,
                name="(in image %s)" % image)
            return [self.viewed_instances[image]]

    def dispLatLon(self):
        if self.position:
            return self.position.dispLatLon()
        else:
            return "(not on earth)"

    def dispMaxPositionDistance(self):
        if len(self.instances) >= 2:
            perimeter = self._positionCollection().perimeter()
            if perimeter:
                return "%.1f m" % perimeter
            else:
                return "(n/a)"
        else:
            return "(n/a)"

    def subfeatures(self):
        return self.instances.values()

    def allowSubfeatures(self):
        return True

    def updateSubfeature(self, feature):
        for image, instance in self.instances.items():
            if instance.id == feature.id:
                self.instances[image] = feature
                return True
        return False

    def setPictureCrop(self, image, size):
        point_of_interest = self.instances.get(image)
        if point_of_interest:
            position = point_of_interest.position
            if position:
                pixel_x, pixel_y = image.invGeoReferencePoint(position)
                offset_position = position_at_offset(position, float(size), 0)
                offset_pixel_x, offset_pixel_y = image.invGeoReferencePoint(
                    offset_position)

                if offset_pixel_x and offset_pixel_y:
                    offset_pixels = max(abs(offset_pixel_x - pixel_x),
                                        abs(offset_pixel_y - pixel_y))

                    self.picture_crop = ImageCrop(image, (pixel_x, pixel_y),
                                                  offset_pixels)


class GroundControlPoint(Point):
    icon_name = "x"
    icon_size = (10, 10)


class Marker(Point):
    icon_name = "flag"
    icon_size = (20, 20)


def load_ground_control_points():
    """
    Returns a list of ground control points (GCP) as defined in the
    ground_control_points.json file.
    """
    location = os.path.join(*["data", "ground_control_points.json"])
    with open(location) as f:
        data = json.load(f)
    ground_control_points = []
    for name, value in data.items():
        position = Position(float(value[0]), float(value[1]))
        ground_control_points.append(
            GroundControlPoint(None, position, name=name))
    return ground_control_points


def load_ground_control_points_Dictionary():
    location = os.path.join(*["data", "ground_control_points.json"])
    with open(location) as f:
        data = json.load(f)
    return data
