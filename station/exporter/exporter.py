"""
Tools for exporting data such as features and locations
into various formats.
"""

import datetime

from lxml import etree
from pykml.factory import KML_ElementMaker as KML
from pykml.factory import GX_ElementMaker as GX
from pykml.parser import Schema

from image import Image
from geo import Position, PositionCollection
from features import Marker

import csv as CSV # For CSV Exporter
from PyQt5 import QtGui

class KMLExporter:
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

        with open(output_path + "features.kml", "wb") as output_file:
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
            for field, value in arg.data:
                # use the str representation of the feature rather than what's in the name field
                # this is done just to exclude the Name from the full description
                if field == "Name":
                    feature_name = str(arg)
                else:
                    feature_full_desc += "%s: %s\n" % (field, str(value))

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

class CSVExporter:
    """
    Provides methods for creating a CSV document populated
    with objects from Pigeon, including marker properties

    Include Anaylasis, CDN, and US competition output styles
    """

    #def __init__(self, output_options=None):
        #Created File Object for csv file
        # self.CSVFileObject = open("exported.csv", 'w+') I guess initialization is not required...
        # Note : w+ for writing and initialize if the file DNE

    def writeMarkersCSV(self, PointsOfIntrest, output_path):
        #Created File Object for csv file
        self.regCSV = open(output_path + "markerResults.csv", 'w+')
        # creates fileObject
        spamWriter = CSV.writer(self.regCSV, delimiter=',')

        currentMarkerList = [] # start with an empty marker list
        titleMissing = True
        titleList = ["Latitude","Longitude"]
        for item in PointsOfIntrest: #Over every marker
            if item.feature.data["Export"] == True: # To be sure we only export things we want to
                currentMarkerList.append(item.feature.position.lat) # Slaps position in the row list
                currentMarkerList.append(item.feature.position.lon)
                for key in item.feature.data: # Add all marker features
                    value = item.feature.data[key]
                    currentMarkerList.append(value)
                    if key in titleList: # Key is in in titleList
                        titleMissing = False # we are on 2nd + marker
                    else: # Assumes keys don't change between markers
                        titleList.append(key) # Ergo this is the first marker
                #if titleMissing:
                 #   titleList.append("Time of Export")
                  #  titleList.append(datetime.datetime.now())
                ExportIndex = titleList.index("Export")
                if titleMissing: # If its the first marker
                    titleList.pop(ExportIndex)
                    spamWriter.writerow(titleList)
                currentMarkerList.pop(ExportIndex)
                spamWriter.writerow(currentMarkerList) #write list as a csv row

            currentMarkerList = [] # clear list for next row

        # Closes CSV so file is updated upon station exit
        self.regCSV.close()

    def writeAreasCSV(self, PointsOfIntrest, output_path):
        #Created File Object for csv file
        self.areasCSV = open(output_path + "areaResults.csv", 'w+')
        # creates fileObject
        spamWriter = CSV.writer(self.areasCSV, delimiter=',', quotechar='|')

        currentMarkerList = [] # start with an empty marker list
        for item in PointsOfIntrest: #Over every marker
            if item.feature.data["Export"] == True: # To be sure we only export things we want to
                currentMarkerList.append(item.feature.position.lat) # Slaps position in the row list
                currentMarkerList.append(item.feature.position.lon)
                currentMarkerList.append(item.feature.image.name)
                for key in item.feature.data:
                    value = item.feature.data[key]
                    currentMarkerList.append(value)
                spamWriter.writerow(currentMarkerList) #write list as a csv row

            currentMarkerList = [] # clear list for next row

        # Closes CSV so file is updated upon station exit
        self.areasCSV.close()

    def writeAUVSIMarkersCSV(self, PointsOfIntrest, output_path):
        #Created File Object for csv file
        self.CSVFileObject = open(output_path + "UAARG.csv", 'w+')
        # creates fileObject
        spamWriter = CSV.writer(self.CSVFileObject, delimiter='\t')

        TargetCount = 0 
        currentMarkerList = [] # start with an empty marker list
        titleMissing = True
        titleList = ["Target Number","Name","Latitude","Longitude"]
        for item in PointsOfIntrest: #Over every marker

            if item.feature.data["Export"] == True: # To be sure we only export things we want to

                TargetCount = TargetCount + 1 # Increment counter
                if TargetCount < 10:
                    currentMarkerList.append("0"+ str(TargetCount))
                else: 
                    currentMarkerList.append(TargetCount)

                latlonDDMMSS = Position.decimal2DegreeMinuiteSeconds([item.feature.position.lat, item.feature.position.lon])
                currentMarkerList.append(latlonDDMMSS[0]) # Slaps position in the row list
                currentMarkerList.append(latlonDDMMSS[1])

                for key in item.feature.data: # Add all marker features
                    value = item.feature.data[key]
                    if key is "Name": # Use Name as Target Type (as it breaks stuff otherwise )
                        currentMarkerList.insert(1, value)
                    else: 
                        currentMarkerList.append(value)
                    if key in titleList: # Key is in in titleList
                        titleMissing = False # we are on 2nd + marker
                    else: # Assumes keys don't change between markers
                        titleList.append(key) # Ergo this is the first marker

                titleList.append("Image Name")
                thumbnailName = str(TargetCount) + "_" + item.feature.image.name

                item.feature.picture.save(output_path + thumbnailName, "PNG")

                currentMarkerList.append(item.feature.image.name)
                #if titleMissing:
                 #   titleList.append("Time of Export")
                  #  titleList.append(datetime.datetime.now())
                ExportIndex = titleList.index("Export")
                
                if titleMissing: # If its the first marker
                    titleList.pop(ExportIndex)
                    NameIndex = titleList.index("Name")
                    titleList.remove("Name")
                    titleList.insert(NameIndex, "Target Type")
                    spamWriter.writerow(titleList)
                currentMarkerList.pop(ExportIndex)
                spamWriter.writerow(currentMarkerList) #write list as a csv row

            currentMarkerList = [] # clear list for next row




        # Closes CSV so file is updated upon station exit
        self.CSVFileObject.close()