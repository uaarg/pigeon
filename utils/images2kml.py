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

from PyQt5 import QtGui, QtWidgets

# Allowing imports from the station directory
sys.path.append(os.path.join(sys.path[0], os.path.pardir, 'station'))

from image import Image
from geo import Position, PositionCollection
from exporter import KMLExporter

image_name_format = "%s.jpg"
info_name_format = "%s.txt"

def image_to_info(image_path):
    """
    Returns the path to the info file associated with the provided image file.
    """
    return image_path.replace(image_name_format % "", info_name_format % "")

class ImageToKML:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)

    def run(self, source_location, destination_location, output_options, validate):
        if os.path.isdir(source_location):
            input_images = glob.glob(os.path.join(*[source_location, image_name_format % "*"]))
        else:
            input_images = [source_location]

        if len(input_images) == 0:
            print("No images at provided location (%s)" % source_location)
        else:
            print("Processing %s images..." % len(input_images))

        kml_exporter = KMLExporter(output_options)

        for input_image in input_images:
            directory, whole_filename = os.path.split(input_image)
            filename, extension = os.path.splitext(whole_filename)

            image = Image(filename, input_image, image_to_info(input_image))
            kml_exporter.processImage(image)

        kml_exporter.writeKML(destination_location, validate)
        print("done.")



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

    output_options = {
              "Output Plane Plumb": args.output_plane_plumb,
              "Output Plane Position": args.output_plane_position,
              "Output Image Outline": args.output_image_outline,
              "Output Image Overlay": args.output_image_overlay,
              "Output Field of View": args.output_field_of_view,
          }
    image_to_kml = ImageToKML()
    image_to_kml.run(args.input_path, args.output, output_options, args.validate)
