#!/usr/bin/env python3
"""
Creates a KML file of the input images. Lots of options allow different
types of KML files to be created (ex. image outlines, plane locations,
image overlays, field of view visualization, etc...)
"""

import sys
import argparse
import os
import glob
import datetime
from lxml import etree
from pykml.factory import KML_ElementMaker as KML
from pykml.factory import GX_ElementMaker as GX
from pykml.parser import Schema

from PyQt5 import QtGui, QtWidgets

# Allowing imports from the station directory
sys.path.append(os.path.join(sys.path[0], os.path.pardir, 'station'))

from image import Image
from geo import Position, PositionCollection

image_name_format = "%s.jpg"
info_name_format = "%s.txt"

def position_collection_to_coordinates(position_collection, close=True):
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

def PigeonKML(arg, **kwargs):
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
        coordinates, altitude_mode = position_collection_to_coordinates(arg)

        output = KML.Placemark(
                        KML.Polygon(
                            KML.altitudeMode(altitude_mode),
                            KML.outerBoundaryIs(
                                KML.LinearRing(
                                    KML.coordinates(coordinates)
                                )
                            )
                        )
                    )

    elif isinstance(arg, Image):
        coordinates, _ = position_collection_to_coordinates(arg.getImageOutline(), close=False)

        output =KML.GroundOverlay(
                        KML.Icon(
                            KML.href(arg.path)
                        ),
                        GX.LatLonQuad(
                            KML.coordinates(coordinates)
                        ),
                        KML.altitudeMode("clampToGround")
                    )
        
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


def image_to_info(image_path):
    """
    Returns the path to the info file associated with the provided image file.
    """
    return image_path.replace(image_name_format % "", info_name_format % "")

class ImageToKML:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)

    def run(self, source_location, destination_location, validate, 
            output_plane_plumb=False,
            output_plane_position=False,
            output_image_outline=False,
            output_image_overlay=False,
            output_field_of_view=False):

        if os.path.isdir(source_location):
            input_images = glob.glob(os.path.join(*[source_location, image_name_format % "*"]))
        else:
            input_images = [source_location]

        if len(input_images) == 0:
            print("No images at provided location (%s)" % source_location)
        else:
            print("Processing %s images..." % len(input_images))

            doc = KML.kml(
                KML.Document(
                    KML.name(datetime.datetime.now())
                )
            )

            for input_image in input_images:

                directory, whole_filename = os.path.split(input_image)
                filename, extension = os.path.splitext(whole_filename)

                folder = KML.Folder(KML.name(filename))
                doc.Document.append(folder)

                image = Image(filename, input_image, image_to_info(input_image))

                if output_plane_plumb:
                    position = image.plane_position.copy()
                    position.alt = None
                    position.height = 0

                    folder.append(
                        PigeonKML(position, description="Plane Plumb"),
                    )

                if output_plane_position:
                    folder.append(
                        PigeonKML(image.plane_position, description="Plane Position")
                    )

                if output_image_outline:
                    self.loadImageSize(image)
                    folder.append(
                        PigeonKML(image.getImageOutline())
                    )

                if output_image_overlay:
                    self.loadImageSize(image)
                    folder.append(PigeonKML(image))

                if output_field_of_view:
                    self.loadImageSize(image)
                    image_corner_positions = image.getImageOutline().getPerimeterPositions()

                    sub_folder = KML.Folder(KML.name("Field Of View"))
                    folder.append(sub_folder)

                    for i in [0, 1, 2, 3]:
                        # Drawing each face of the pyramid as a separate polygon
                        field_of_view_face = PositionCollection([image_corner_positions[i], image_corner_positions[i+1], image.plane_position])

                        sub_folder.append(
                            PigeonKML(field_of_view_face)
                        )


            if validate:
                # Validate the KML:
                schema = Schema("ogckml22.xsd")
                schema.assertValid(doc)

            # Write the KML file:
            with open(destination_location, "wb") as output_file:
                output_file.write(etree.tostring(doc, pretty_print=True))

            print("done.")

    def loadImageSize(self, image):
        if not image.width or not image.height:            
            pixmap = QtGui.QPixmap(image.path)
            image.width = pixmap.width()
            image.height = pixmap.height()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create a KML file with the information provided by input images.')
    parser.add_argument("input_path", type=str, default=".", help="Path to the image(s) (file or folder) to use.")
    parser.add_argument("--output-plane-plumb",    action="store_true", help="Output the plane plumb.")
    parser.add_argument("--output-plane-position", action="store_true", help="Output the plane position.")
    parser.add_argument("--output-image-outline",  action="store_true", help="Output the image outline.")
    parser.add_argument("--output-image-overlay",  action="store_true", help="Output the image overlay.")
    parser.add_argument("--output-field-of-view",  action="store_true", help="Output the field of view.")

    parser.add_argument("--validate", action="store_true", help="Check that the output is valid KML (not enabled by default because it seems to give false positives).")
    parser.add_argument("-o", "--output", type=str, default="output.kml", help="Path specifying the output file.")
    args = parser.parse_args()

    if not args.output_plane_plumb and not args.output_plane_position and not args.output_image_outline and not args.output_image_overlay and not args.output_field_of_view:
        parser.error("At least one of the output options must be specified to produce a KML with anything in it.")

    image_to_kml = ImageToKML()
    image_to_kml.run(args.input_path, args.output, validate=args.validate, 
            output_plane_plumb=args.output_plane_plumb,
            output_plane_position=args.output_plane_position,
            output_image_outline=args.output_image_outline,
            output_image_overlay=args.output_image_overlay,
            output_field_of_view=args.output_field_of_view)