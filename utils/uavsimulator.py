#!/usr/bin/env python3
"""
Simulates the onboard imaging code: interfaces with the ground station
as if it were the plane. Provides:

* Puts images and info files into the monitored folder.
"""

from __future__ import division

import os
import shutil
import glob
import time
import sys
import argparse

try:
    input = raw_input # Python 2
except NameError:
    pass # Python 3

image_source_location = os.path.join(*["data", "images"])

# Change this based on where you want images to go to!!
image_destination_location = os.path.join(*[os.pardir, "station", "data", "images"])
image_name_format = "%s.jpg"
info_name_format = "%s.txt"

class Finished(Exception):
    pass

def image_to_info(image_path):
    """
    Returns the path to the info file associated with the provided image file.
    """
    return image_path.replace(image_name_format % "", info_name_format % "")

class UavImaging():
    def __init__(self):
        input_path = os.path.join(*[image_source_location, image_name_format % "*"])
        self.input_images = glob.glob(input_path)
        print("Found " + str(len(self.input_images)) + " images at " + input_path)
        # Sorts the image by its name. So that sim actually looks realistic
        self.input_images = sorted(self.input_images)
        self.output_images = []
        self.input_image_index = 0
        self.output_image_index = 1

    def run(self, transmission_rate=0.5, number_of_images=None, wait=False):
        try:
            while True:
                if number_of_images is not None:
                    if self.output_image_index > number_of_images:
                        print("Transmitted %s images." % number_of_images)
                        raise(Finished())

                print("Transmitting image %s..." % self.output_image_index)
                output_image = os.path.join(*[image_destination_location, image_name_format % self.output_image_index])
                print(output_image)
                self.output_images.append(output_image)
                shutil.copy(self.input_images[self.input_image_index], output_image)
                shutil.copy(image_to_info(self.input_images[self.input_image_index]), image_to_info(output_image))

                self.input_image_index += 1
                if self.input_image_index >= len(self.input_images):
                    self.input_image_index = 0

                self.output_image_index += 1

                time.sleep(1/transmission_rate)

        except (KeyboardInterrupt, Finished):
            if wait:
                try:
                    _ = input("\nStopping. Waiting on input to start cleanup... ")
                except KeyboardInterrupt:
                    pass

            print("\nCleanup up...")
            print("Removing copied images...")
            for output_image in self.output_images:
                os.remove(output_image)
                os.remove(image_to_info(output_image))
            print("Done.\n")
            sys.exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simulate transmission of images from a uav by simply copying them to the target directory.')
    parser.add_argument("--transmission_rate", "-r", type=float, default=3, help="The number of images to transfer per second")
    parser.add_argument("--number_of_images", "-n", type=int, default=None, help="Stop after transmitting this many images")
    parser.add_argument("--wait", "-w", action="store_true", default=False, help="Don't cleanup immediately: wait for second KeyboardInterrupt")
    args = parser.parse_args()

    uav_imaging = UavImaging()
    uav_imaging.run(transmission_rate=args.transmission_rate, number_of_images=args.number_of_images, wait=args.wait)
