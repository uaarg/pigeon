#!/usr/bin/env python3
"""
Simulates the onboard imaging code: interfaces with the ground station
as if it were the plane. Provides:

* Puts images into the monitored folder.
"""

import os
import shutil
import glob
import time

image_source_location = os.path.join(*["data", "images"])
image_destination_location = os.path.join(*[os.pardir, "station", "data", "images"])
image_name_format = "%s.jpg"
info_name_format = "%s.txt"

image_transmission_rate = 0.5 # Images per second

def image_to_info(image_path):
    """
    Returns the path to the info file associated with the provided image file.
    """
    return image_path.replace(image_name_format % "", info_name_format % "")

class UavImaging():
    def __init__(self):
        self.input_images = glob.glob(os.path.join(*[image_source_location, image_name_format % "*"]))
        self.output_images = []
        self.input_image_index = 0
        self.output_image_index = 1
    def run(self):
        try:
            while True:
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

                time.sleep(1/image_transmission_rate)

        except KeyboardInterrupt:
            print("\nCleanup up...")
            print("Removing copied images...")
            for output_image in self.output_images:
                os.remove(output_image)
                os.remove(image_to_info(output_image))
            raise


if __name__ == "__main__":
    uav_imaging = UavImaging()
    uav_imaging.run()