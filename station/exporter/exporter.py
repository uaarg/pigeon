"""
Tools for exporting data such as features and locations
into various formats.
"""

import datetime
import os

from lxml import etree
from pykml.factory import KML_ElementMaker as KML
from pykml.factory import GX_ElementMaker as GX
from pykml.parser import Schema

from image import Image
from geo import Position, PositionCollection
from features import Marker

import csv as CSV # For CSV Exporter
from PyQt5 import QtGui, QtCore

from .common import Exporter
from .interop_exporter import InteropClient


class KMLExporter(Exporter):
    """
    Provides methods for creating a KML document populated
    with objects from Pigeon, including aircraft and marker
    locations.
    """

    def __init__(self, output_options=None):
        # Initialize KML doc
        self.doc = KML.kml(
                KML.Document(
                    KML.name(datetime.datetime.now())
                )
            )

        self.output_options = output_options

        # Creating necessary styles:
        if self.output_options and self.output_options.get("Output Field of View"):
            self.doc.Document.append(
                KML.Style(
                    KML.PolyStyle(
                        KML.color("00ffffff")
                    ),
                    id="outline_only_polygon"
                )
            )

    def export(self, features, path):
        for feature in features:
            if isinstance(feature, Marker):
                self.doc.Document.append(
                    self.classToKML(feature)
                )

        self.writeKML(path)

    def processImage(self, image):
        """
        Creates a KML folder for a single image
        and populates it with KML elements from image properties.
        """
        # Define which objects to export
        self.output_plane_plumb = self.output_options["Output Plane Plumb"]
        self.output_plane_position = self.output_options["Output Plane Position"]
        self.output_image_outline = self.output_options["Output Image Outline"]
        self.output_image_overlay = self.output_options["Output Image Overlay"]
        self.output_field_of_view = self.output_options["Output Field of View"]

        folder = KML.Folder(KML.name(image.name))
        self.doc.Document.append(folder)

        if self.output_plane_plumb:
            position = image.plane_position.copy()
            position.alt = None
            position.height = 0

            folder.append(
                self.classToKML(position, description="Plane Plumb"),
            )

        if self.output_plane_position:
            folder.append(
                self.classToKML(image.plane_position, description="Plane Position")
            )

        if self.output_image_outline:
            self.loadImageSize(image)
            folder.append(
                self.classToKML(image.getImageOutline())
            )

        if self.output_image_overlay:
            self.loadImageSize(image)
            folder.append(self.classToKML(image))

        if self.output_field_of_view:
            self.loadImageSize(image)
            image_corner_positions = image.getImageOutline().getPerimeterPositions()

            sub_folder = KML.Folder(KML.name("Field Of View"))
            folder.append(sub_folder)

            for i in [0, 1, 2, 3]:
                # Drawing each face of the pyramid as a separate polygon
                field_of_view_face = PositionCollection([image_corner_positions[i], image_corner_positions[i+1], image.plane_position])

                sub_folder.append(
                    self.classToKML(field_of_view_face)
                )

    def loadImageSize(self, image):
        if not image.width or not image.height:
            pixmap = QtGui.QPixmap(image.path)
            image.width = pixmap.width()
            image.height = pixmap.height()

    def writeKML(self, output_path, validate=False):
        """
        Writes the KML document currently held by the object to file.
        """
        if validate:
            schema = Schema("ogckml22.xsd")
            schema.assertValid(doc)

        with open(os.path.join(output_path, "features.kml") , "wb") as output_file:
            output_file.write(etree.tostring(self.doc, pretty_print=True))

    def classToKML(self, arg, **kwargs):
        """
        Function for converting instances of pigeon-defined Classes into
        pykml representations. Ex. maps a Position instance to a KML
        Point Placemark.
        """

        if isinstance(arg, Position):
            output = KML.Placemark(
                            KML.Point(
                                KML.coordinates("%s,%s,%s" % (arg.lon, arg.lat, arg.alt or 0))
                            )
                        )

            if arg.alt:
                output.Point.append(KML.altitudeMode("absolute"))

        elif isinstance(arg, PositionCollection):
            coordinates, altitude_mode = self._position_collection_to_coordinates(arg)

            output = KML.Placemark(
                            KML.Polygon(
                                KML.altitudeMode(altitude_mode),
                                KML.outerBoundaryIs(
                                    KML.LinearRing(
                                        KML.coordinates(coordinates)
                                    )
                                )
                            ),
                            KML.styleUrl("#outline_only_polygon")
                        )

        elif isinstance(arg, Image):
            coordinates, _ = self._position_collection_to_coordinates(arg.getImageOutline(), close=False)

            output = KML.GroundOverlay(
                            KML.Icon(
                                KML.href(arg.path)
                            ),
                            GX.LatLonQuad(
                                KML.coordinates(coordinates)
                            ),
                            KML.altitudeMode("clampToGround")
                        )

        elif isinstance(arg, Marker):
            feature_full_desc = ""
            for key, value in arg.data:
                # use the str representation of the feature rather than what's in the name field
                # this is done just to exclude the Name from the full description
                key = field[0]
                value = field[1]
                if key == "Name":
                    feature_name = str(arg)
                else:
                    feature_full_desc += "%s: %s\n" % (key, str(value))

                pos = arg.position
                output = KML.Placemark(
                            KML.name(feature_name),
                            KML.Point(
                                KML.coordinates("%s,%s,%s" % (pos.lon, pos.lat, pos.alt or 0))
                            ),
                            KML.description(feature_full_desc)
                        )
                if pos.alt:
                    output.Point.append(KML.altitudeMode("absolute"))

        else:
            raise(Exception("Type %s not supported yet." % arg.__class__.__name__))

        # Allowing normal KML elements to be added to the top level of
        # the element created. This deviates from the pykml way of doing
        # things, but it works for now.
        if kwargs:
            for key, value in kwargs.items():
                kml_element_type = getattr(KML, key)
                kml_element = kml_element_type(value)
                output.append(kml_element)

        return output

    def _position_collection_to_coordinates(self, position_collection, close=True):
        """
        Returns a tuple with two elements. The first element is a string
        suitable for use in a KML "coordinates" element with the positions
        from the position_collection. If close=True, the last position is
        guaranteed to be the same as the first (necessary ex. for Polygons).
        The second element is a string with a suggested altitudeMode value
        (ex. clampToGround, absolute, etc...). This is determined based on
        whether all the positions in the position_collection have a height
        value, altitude value, etc...
        """
        coordinates = ""
        altitude_mode = None
        largest_z = 0
        for position in position_collection.getPerimeterPositions(close=close):

            # Plotting polygon three-dimensinally, according to whether
            # positions have height or alt data. All points should have
            # matching data to avoid errors.
            if position.height is not None:
                if altitude_mode and altitude_mode != "relativeToGround":
                    raise ValueError("Position collection contains some position(s) with height but not all.")
                z = position.height
                altitude_mode = "relativeToGround"
            elif position.alt is not None:
                if altitude_mode and altitude_mode != "absolute":
                    raise ValueError("Position collection contains some position(s) with alt but not all.")
                z = position.alt
                altitude_mode = "absolute"
            else:
                altitude_mode = "clampToGround"
                z = 0

            largest_z = max(z, largest_z)

            coordinates += "%s,%s,%s " % (position.lon, position.lat, z)

        if largest_z <= 0:
            altitude_mode = "clampToGround"

        return coordinates, altitude_mode

class CSVExporter(Exporter):
    """
    Provides methods for creating a CSV document populated
    with objects from Pigeon, including marker properties

    Include Anaylasis, and US competition output styles
    """

    def export(self, features, output_path):
        self.writeMarkersCSV([feature for feature in features if isinstance(feature, Marker)], output_path)

    def writeMarkersCSV(self, features, output_path):
        #Created File Object for csv file
        self.CSVFileObject = open(os.path.join(output_path, "markerResults.csv") , 'w+')
        # creates fileObject
        spamWriter = CSV.writer(self.CSVFileObject, delimiter=',', quotechar='|')

        spamWriter.writerow(["Latitude", "Longitude", "Colour","Letter", "Notes",
                            "Time of Export",datetime.datetime.now()])

        currentMarkerList = [] # start with an empty marker list
        for feature in features: #Over every marker
            currentMarkerList.append(feature.position.lat) # Slaps position in the row list
            currentMarkerList.append(feature.position.lon)
            for data_column in ["Colour", "Letter", "Notes"]:
                for field in feature.data:
                    key = field[0]
                    value = field[1]
                    if key == data_column:
                        currentMarkerList.append(value)
                        break
                else:
                    currentMarkerList.append("")

            spamWriter.writerow(currentMarkerList) #write list as a csv row

            currentMarkerList = [] # clear list for next row

        # Closes CSV so file is updated upon station exit
        self.CSVFileObject.close()

class AUVSICSVExporter(Exporter):
    def export(self, features, output_path):
        self.writeAUVSIMarkersCSV([feature for feature in features if isinstance(feature, Marker)], output_path)

    def writeAUVSIMarkersCSV(self, PointsOfIntrest, output_path):
        #Created File Object for csv file
        self.CSVFileObject = open(os.path.join(output_path, "UAARG.csv") , 'w+')
        # creates fileObject
        spamWriter = CSV.writer(self.CSVFileObject, delimiter='\t')

        TargetCount = 0
        currentMarkerList = [] # start with an empty marker list
        titleMissing = True

        for marker in PointsOfIntrest: #Over every marker
            titleList = ["Target Number","Latitude","Longitude"]
            TargetCount = TargetCount + 1 # Increment counter
            currentMarkerList.append("%02d" % TargetCount)

            latlonDDMMSS = marker.position.dispLatLonDDMMSS()
            currentMarkerList.append(latlonDDMMSS[0]) # Slaps position in the row list
            currentMarkerList.append(latlonDDMMSS[1])
            for data_column in ["Type", "Orientation", "Shape", "Bkgnd_Color", "Alphanumeric", "Alpha_Color", "Notes"]:
                for field  in marker.data: # Add all marker features we care about
                    key = field[0]
                    value = field[1]
                    if key == data_column:
                        currentMarkerList.append(value)
                        break
                else:
                    currentMarkerList.append("")
            print(currentMarkerList)
            titleList.extend(("Type", "Orientation", "Shape", "Bkgnd_Color", "Alphanumeric", "Alpha_Color", "Notes"))

            titleList.insert(9,"Image Name")
            thumbnailName = "Targ_" + str(TargetCount)

            cropping_rect = QtCore.QRect(QtCore.QPoint(*marker.picture_crop.top_left), QtCore.QPoint(*marker.picture_crop.bottom_right))
            original_picture = marker.picture_crop.image.pixmap_loader.getPixmapForSize(None)
            picture = original_picture.copy(cropping_rect)

            picture.save(os.path.join(output_path, thumbnailName), "JPG")
            currentMarkerList.insert( 9,thumbnailName + ".jpg")

            if (TargetCount == 1):
                spamWriter.writerow(titleList) #write list as a csv row
            spamWriter.writerow(currentMarkerList) #write list as a csv row

            currentMarkerList = [] # clear list for next row
            titleList = []
        # Closes CSV so file is updated upon station exit
        self.CSVFileObject.close()


class AUVSI(Exporter):
    """
    Runs both the AUVSI CSV exporter and the Interop Exporter.
    """
    def __init__(self):
        self.csv_exporter = AUVSICSVExporter()
        self.interop_exporter = InteropClient()

    def export(self, features, output_path):
        self.csv_exporter.export(features, output_path)
        self.interop_exporter.export(features, output_path)


class ExportManager:
    def __init__(self, path):
        self.path = path
        self.options = [
                            ("KML", self._generateExporterFunc(KMLExporter), None),
                            ("CSV Normal", self._generateExporterFunc(CSVExporter), None),
                            ("AUVSI CSV", self._generateExporterFunc(AUVSICSVExporter), None),
                            ("AUVSI Interop", self._generateExporterFunc(InteropClient), "Ctrl+E"),
                            ("AUVSI CSV + Interop", self._generateExporterFunc(AUVSI), None),
                       ]

    def _generateExporterFunc(self, exporter):
        def func(features):
            exporter().export(self.featuresToExport(features), self.path)
        return func

    def featuresToExport(self, features):
        exportable = []
        for feature in features:
            for field in feature.data:
                key = field[0]
                value = field[1]
                if key == "Export":
                    if value:
                        exportable.append(feature)
                        break
        return exportable
